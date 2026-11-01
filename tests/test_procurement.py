from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import SCALEUserRole
from apps.inventory.models import Warehouse, ProductCategory, Product, InventoryBalance
from apps.suppliers.models import Supplier, SupplierProduct, SupplierStatus, PaymentTerms
from apps.procurement.models import ProcurementPolicy, PurchaseOrder, POStatus, POCategory
from apps.procurement.services import AutonomousProcurementService
from apps.suppliers.services import SupplierEvaluationService
from apps.audit.models import AuditLog

User = get_user_model()


class ProcurementAndSupplierTests(TestCase):
    """
    Test suite for Phase 5: Autonomous Procurement Engine & Supplier Management.
    """

    def setUp(self):
        self.manager = User.objects.create_user(username='mgr_po', password='Password123!', role=SCALEUserRole.MANAGER)
        self.employee = User.objects.create_user(username='emp_po', password='Password123!', role=SCALEUserRole.EMPLOYEE)

        self.wh = Warehouse.objects.create(code='WH-PO-01', name='Procurement Test Facility')
        self.cat = ProductCategory.objects.create(code='CAT-PO', name='Electronics')
        self.product = Product.objects.create(
            sku='SKU-PO-777',
            name='Industrial Controller Board',
            category=self.cat,
            unit_cost=Decimal('20.00'),
            unit_price=Decimal('35.00'),
            reorder_point=Decimal('300.00'),
            safety_stock=Decimal('80.00'),
            minimum_order_qty=Decimal('50.00'),
            order_multiple=Decimal('10.00')
        )
        self.balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.wh,
            on_hand_stock=Decimal('50.00'),
            reserved_stock=Decimal('0.00'),
            incoming_stock=Decimal('0.00')
        )

        self.supplier = Supplier.objects.create(
            code='SUPP-TEST-01',
            legal_name='Apex Electronics Ltd',
            email='sales@apex.internal',
            reliability_score=Decimal('95.00'),
            quality_score=Decimal('95.00'),
            lead_time_compliance_rate=Decimal('95.00'),
            status=SupplierStatus.ACTIVE
        )
        SupplierProduct.objects.create(
            supplier=self.supplier,
            product=self.product,
            contracted_unit_price=Decimal('20.00'),
            lead_time_days=5,
            is_preferred=True
        )

        self.policy = ProcurementPolicy.objects.create(
            policy_name='Standard Policy',
            auto_dispatch_max_value=Decimal('5000.00'),
            require_approval_above_value=Decimal('5000.00'),
            min_supplier_reliability_score=Decimal('80.00')
        )

    def test_supplier_evaluation_and_ranking(self):
        """Verify multi-factor supplier scoring (Part 12.2)."""
        ranked = SupplierEvaluationService.evaluate_and_rank_suppliers(self.product)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]['supplier_code'], 'SUPP-TEST-01')
        self.assertEqual(ranked[0]['composite_score'], Decimal('95.00'))

    def test_category_b_autonomous_dispatch_under_ceiling(self):
        """Verify orders <= $5,000 auto-dispatch as Category B (Part 12.3)."""
        # Order 100 units @ $20.00 = $2,000.00 <= $5,000 ceiling
        po = AutonomousProcurementService.generate_replenishment_order(
            product=self.product,
            warehouse=self.wh,
            order_quantity=Decimal('100.00'),
            actor=self.manager
        )
        self.assertEqual(po.category, POCategory.CATEGORY_B)
        self.assertEqual(po.status, POStatus.DISPATCHED)
        self.assertIsNotNone(po.dispatched_at)

        # Incoming stock on inventory balance should be incremented
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.incoming_stock, Decimal('100.00'))

    def test_category_c_escalation_above_ceiling(self):
        """Verify orders > $5,000 route to AWAITING_APPROVAL as Category C (Part 12.3)."""
        # Order 350 units @ $20.00 = $7,000.00 > $5,000 ceiling
        po = AutonomousProcurementService.generate_replenishment_order(
            product=self.product,
            warehouse=self.wh,
            order_quantity=Decimal('350.00'),
            actor=self.manager
        )
        self.assertEqual(po.category, POCategory.CATEGORY_C)
        self.assertEqual(po.status, POStatus.AWAITING_APPROVAL)
        self.assertIsNone(po.dispatched_at)

        # Supervisor approves the order
        AutonomousProcurementService.approve_purchase_order(po, supervisor=self.manager)
        po.refresh_from_db()
        self.assertEqual(po.status, POStatus.DISPATCHED)
        self.assertEqual(po.approved_by, self.manager)
        self.assertIsNotNone(po.dispatched_at)

    def test_employee_cannot_approve_category_c_order(self):
        """Verify non-manager users cannot authorize purchase orders (Part 6.1)."""
        po = AutonomousProcurementService.generate_replenishment_order(
            product=self.product,
            warehouse=self.wh,
            order_quantity=Decimal('400.00'),
            actor=self.manager
        )
        with self.assertRaises(ValidationError):
            AutonomousProcurementService.approve_purchase_order(po, supervisor=self.employee)
