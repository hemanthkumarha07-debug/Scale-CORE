from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import SCALEUserRole
from apps.inventory.models import Warehouse, ProductCategory, Product, InventoryBalance, MovementType, ABCClass, XYZClass, ReconciliationStatus
from apps.inventory.services import StockMovementService, InventoryClassificationService, StockReconciliationService
from apps.sales.models import DailySalesLog
from apps.audit.models import AuditLog

User = get_user_model()


class InventoryIntelligenceTests(TestCase):
    """
    Test suite for Phase 3: Inventory Intelligence Engine.
    Covers stock movements, balance tracking, ABC/XYZ classification, and reconciliation.
    """

    def setUp(self):
        self.manager = User.objects.create_user(username='mgr_inv', password='Password123!', role=SCALEUserRole.MANAGER)
        self.wh = Warehouse.objects.create(code='WH-INV-01', name='Testing Hub')
        self.cat = ProductCategory.objects.create(code='CAT-E', name='Electronics')
        self.product = Product.objects.create(
            sku='SKU-INV-999',
            name='Precision Sensor Probe',
            category=self.cat,
            unit_cost=Decimal('50.00'),
            unit_price=Decimal('85.00'),
            reorder_point=Decimal('200.00'),
            safety_stock=Decimal('60.00')
        )
        self.balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.wh,
            on_hand_stock=Decimal('100.00')
        )

    def test_stock_movement_inbound_and_audit(self):
        """Verify inbound movement increases on-hand stock and creates audit entry."""
        initial_stock = self.balance.on_hand_stock
        movement = StockMovementService.record_movement(
            product=self.product,
            warehouse=self.wh,
            movement_type=MovementType.GOODS_RECEIPT,
            quantity=Decimal('50.00'),
            reference_doc_type='PurchaseOrder',
            reference_doc_id='PO-999',
            performed_by=self.manager,
            notes='Dock arrival'
        )

        self.balance.refresh_from_db()
        self.assertEqual(self.balance.on_hand_stock, Decimal('150.00'))
        self.assertEqual(movement.balance_before, initial_stock)
        self.assertEqual(movement.balance_after, Decimal('150.00'))

        # Verify audit log recorded
        audit = AuditLog.objects.filter(entity_type='INVENTORY_BALANCE').order_by('-timestamp').first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.state_after['on_hand_stock'], '150.00')

    def test_stock_movement_outbound_insufficient_stock_fails(self):
        """Verify outbound movement fails if stock goes negative."""
        with self.assertRaises(ValidationError):
            StockMovementService.record_movement(
                product=self.product,
                warehouse=self.wh,
                movement_type=MovementType.SALES_DISPATCH,
                quantity=Decimal('-250.00'),
                performed_by=self.manager
            )

    def test_abc_and_xyz_classification(self):
        """Verify automated ABC and XYZ categorization logic."""
        # Create sales records with varying demand
        today = timezone.now().date()
        for i in range(15):
            d = today - timezone.timedelta(days=i)
            DailySalesLog.objects.create(
                date=d,
                product=self.product,
                warehouse=self.wh,
                units_sold=Decimal('10.00'),
                sales_revenue=Decimal('850.00'),
                was_stockout_day=False
            )

        abc_counts = InventoryClassificationService.run_abc_analysis()
        xyz_counts = InventoryClassificationService.run_xyz_analysis()

        self.product.refresh_from_db()
        self.assertIn(self.product.abc_class, [ABCClass.A, ABCClass.B, ABCClass.C])
        # Since demand is exactly 10 units each day, standard deviation is 0 -> CV = 0 <= 0.10 -> Class X
        self.assertEqual(self.product.xyz_class, XYZClass.X)

    def test_stock_reconciliation_workflow(self):
        """Verify physical count reconciliation and approved adjustments."""
        rec = StockReconciliationService.create_batch(warehouse=self.wh, assigned_to=self.manager)
        self.assertEqual(rec.status, ReconciliationStatus.DRAFT)
        self.assertEqual(rec.items.count(), 1)

        item = rec.items.first()
        self.assertEqual(item.system_quantity, Decimal('100.00'))
        # Set physical count to 95 (discrepancy of -5 units)
        item.physical_quantity = Decimal('95.00')
        item.save()

        # Approve reconciliation
        StockReconciliationService.approve_reconciliation(rec, supervisor=self.manager)
        rec.refresh_from_db()
        self.assertEqual(rec.status, ReconciliationStatus.APPROVED)

        # On-hand stock should now be adjusted to 95.00
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.on_hand_stock, Decimal('95.00'))
