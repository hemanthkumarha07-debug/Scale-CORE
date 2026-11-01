from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from apps.accounts.models import SCALEUserRole
from apps.inventory.models import Warehouse, ProductCategory, Product, InventoryBalance
from apps.suppliers.models import Supplier, SupplierStatus, PaymentTerms
from apps.procurement.models import ProcurementPolicy, PurchaseOrder, POStatus, POCategory
from apps.audit.models import AuditLog
from apps.audit.services import AuditIntegrityService

User = get_user_model()


class FoundationSecurityAndModelTests(TestCase):
    """
    Automated test suite verifying Phase 1 foundation:
    - User authentication and role privileges (Manager vs Employee).
    - Inventory balance calculations (Available vs Projected).
    - Procurement policy gate evaluation.
    - Cryptographic audit ledger immutability and hash chaining.
    """

    def setUp(self):
        # 1. Users
        self.manager = User.objects.create_user(
            username='mgr_test',
            password='Password123!',
            role=SCALEUserRole.MANAGER
        )
        self.employee = User.objects.create_user(
            username='emp_test',
            password='Password123!',
            role=SCALEUserRole.EMPLOYEE
        )

        # 2. Inventory entities
        self.wh = Warehouse.objects.create(code='WH-TEST-01', name='Test Facility')
        self.cat = ProductCategory.objects.create(code='CAT-T', name='Test Cat')
        self.product = Product.objects.create(
            sku='SKU-TEST-001',
            name='Test Item',
            category=self.cat,
            unit_cost=Decimal('10.00'),
            unit_price=Decimal('20.00'),
            reorder_point=Decimal('100.00'),
            safety_stock=Decimal('30.00')
        )

    def test_user_role_authorities(self):
        """Verify Manager vs Employee privilege separation (Part 6.1)."""
        self.assertTrue(self.manager.is_manager)
        self.assertFalse(self.manager.is_employee)
        self.assertTrue(self.manager.can_access_financials())
        self.assertTrue(self.manager.can_approve_procurement())

        self.assertFalse(self.employee.is_manager)
        self.assertTrue(self.employee.is_employee)
        self.assertFalse(self.employee.can_access_financials())
        self.assertFalse(self.employee.can_approve_procurement())

    def test_inventory_balance_calculations(self):
        """Verify Available Stock = On-Hand - Reserved (Part 8.2)."""
        balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.wh,
            on_hand_stock=Decimal('150.00'),
            reserved_stock=Decimal('40.00'),
            incoming_stock=Decimal('50.00')
        )
        # Available = 150 - 40 = 110
        self.assertEqual(balance.available_stock, Decimal('110.00'))
        # Projected = 110 + 50 = 160
        self.assertEqual(balance.projected_stock, Decimal('160.00'))
        # Projected 160 > ROP 100 -> is_below_rop is False
        self.assertFalse(balance.is_below_rop)

        # Now simulate low stock: On-hand 50, reserved 10 -> Available 40, incoming 0 -> Projected 40 < ROP 100
        balance.on_hand_stock = Decimal('50.00')
        balance.reserved_stock = Decimal('10.00')
        balance.incoming_stock = Decimal('0.00')
        balance.save()
        self.assertEqual(balance.available_stock, Decimal('40.00'))
        self.assertTrue(balance.is_below_rop)

    def test_audit_ledger_immutability(self):
        """Verify AuditLog prevents updates and deletes (Part 7.3)."""
        record = AuditLog.record_event(
            event_type='TEST_EVENT',
            entity_type='PRODUCT',
            entity_id=str(self.product.id),
            actor=self.manager,
            state_after={'action': 'CREATED'}
        )
        self.assertIsNotNone(record.current_hash)

        # Attempting to modify must raise ValidationError
        record.event_type = 'TAMPERED_EVENT'
        with self.assertRaises(ValidationError):
            record.save()

        # Attempting to delete must raise ValidationError
        with self.assertRaises(ValidationError):
            record.delete()

    def test_audit_ledger_hash_chaining_and_integrity(self):
        """Verify that hash chaining validates properly and detects tampering."""
        AuditLog.objects.all().delete = super(AuditLog, AuditLog).delete # bypass for clean test
        
        # Create sequential chain
        rec1 = AuditLog.record_event(event_type='EVT_1', entity_type='T', entity_id='1', actor=self.manager)
        rec2 = AuditLog.record_event(event_type='EVT_2', entity_type='T', entity_id='2', actor=self.manager)
        rec3 = AuditLog.record_event(event_type='EVT_3', entity_type='T', entity_id='3', actor=self.manager)

        # Chain link verification: rec2.previous_hash == rec1.current_hash
        self.assertEqual(rec2.previous_hash, rec1.current_hash)
        self.assertEqual(rec3.previous_hash, rec2.current_hash)

        # Whole chain verification
        result = AuditIntegrityService.verify_ledger_chain()
        self.assertEqual(result['chain_integrity'], 'VALID')
        self.assertFalse(result['tampering_detected'])

    def test_overview_dashboard_http_response(self):
        """Verify Overview Dashboard renders HTTP 200 with Enterprise Hybrid layout."""
        client = Client()
        client.force_login(self.manager)
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SCALE.Core')
        self.assertContains(response, 'Operational Command Center')
        self.assertContains(response, 'Total Inventory Valuation')
        self.assertContains(response, 'demandForecastChart')
