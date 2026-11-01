from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.accounts.models import SCALEUserRole
from apps.inventory.models import Warehouse, ProductCategory, Product, InventoryBalance
from apps.suppliers.models import Supplier, SupplierProduct, SupplierStatus
from apps.procurement.models import PurchaseOrder, PurchaseOrderItem, POStatus, POCategory
from apps.logistics.models import Shipment, GoodsReceipt, ShipmentStatus
from apps.logistics.services import LogisticsService
from apps.system_health.services import SystemHealthProbeService
from apps.system_health.models import HealthStatus

User = get_user_model()


class LogisticsAndSystemHealthTests(TestCase):
    """
    Test suite for Phase 6: Logistics & Goods Receipt and Phase 10: System Health Probes.
    """

    def setUp(self):
        self.operator = User.objects.create_user(username='dock_op', password='Password123!', role=SCALEUserRole.EMPLOYEE)
        self.manager = User.objects.create_user(username='mgr_log', password='Password123!', role=SCALEUserRole.MANAGER)

        self.wh = Warehouse.objects.create(code='WH-LOG-01', name='Logistics Terminal')
        self.cat = ProductCategory.objects.create(code='CAT-LOG', name='Hardware')
        self.product = Product.objects.create(
            sku='SKU-LOG-555',
            name='Industrial Servo Motor',
            category=self.cat,
            unit_cost=Decimal('80.00'),
            unit_price=Decimal('130.00'),
            reorder_point=Decimal('100.00'),
            safety_stock=Decimal('30.00')
        )
        self.balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.wh,
            on_hand_stock=Decimal('20.00'),
            reserved_stock=Decimal('0.00'),
            incoming_stock=Decimal('50.00')
        )

        self.supplier = Supplier.objects.create(
            code='SUPP-LOG-01',
            legal_name='Precision Motors Ltd',
            reliability_score=Decimal('90.00'),
            quality_score=Decimal('90.00'),
            lead_time_compliance_rate=Decimal('90.00'),
            status=SupplierStatus.ACTIVE
        )

        self.po = PurchaseOrder.objects.create(
            po_number='PO-LOG-0001',
            supplier=self.supplier,
            warehouse=self.wh,
            total_amount=Decimal('4000.00'),
            status=POStatus.DISPATCHED,
            category=POCategory.CATEGORY_B,
            expected_delivery_date=timezone.now().date() + timezone.timedelta(days=5)
        )
        self.po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.po,
            product=self.product,
            quantity=Decimal('50.00'),
            unit_price=Decimal('80.00')
        )

        self.shipment = Shipment.objects.create(
            tracking_number='TRK-999888',
            purchase_order=self.po,
            carrier_name='BlueDart Freight',
            dispatch_date=timezone.now().date(),
            expected_delivery_date=timezone.now().date() + timezone.timedelta(days=3),
            status=ShipmentStatus.IN_TRANSIT
        )

    def test_goods_receipt_processing_and_stock_increment(self):
        """Verify dock arrival increments on-hand stock and completes purchase order (Part 14.2)."""
        initial_on_hand = self.balance.on_hand_stock
        receipt = LogisticsService.process_goods_receipt(
            purchase_order=self.po,
            received_items=[{'product_id': self.product.id, 'quantity_received': 50.0, 'quantity_damaged': 0}],
            operator=self.operator,
            shipment=self.shipment,
            notes='All 50 units inspected and verified'
        )

        self.assertEqual(receipt.discrepancy_detected, False)

        # On-hand stock should increase by 50 units (20 + 50 = 70)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.on_hand_stock, Decimal('70.00'))

        # Incoming stock should be reduced
        self.assertEqual(self.balance.incoming_stock, Decimal('0.00'))

        # Purchase order status must be COMPLETED
        self.po.refresh_from_db()
        self.assertEqual(self.po.status, POStatus.COMPLETED)
        self.assertEqual(self.po.items.first().quantity_received, Decimal('50.00'))

        # Shipment status must be DELIVERED
        self.shipment.refresh_from_db()
        self.assertEqual(self.shipment.status, ShipmentStatus.DELIVERED)

    def test_goods_receipt_discrepancy_detection(self):
        """Verify delivery discrepancies (shortages/damages) are flagged (Part 14.2)."""
        receipt = LogisticsService.process_goods_receipt(
            purchase_order=self.po,
            received_items=[{'product_id': self.product.id, 'quantity_received': 40.0, 'quantity_damaged': 5}],
            operator=self.operator,
            shipment=self.shipment,
            notes='5 units damaged in crate'
        )
        self.assertTrue(receipt.discrepancy_detected)

    def test_system_health_probes(self):
        """Verify empirical subsystem probing (Part 21)."""
        db_probe = SystemHealthProbeService.probe_database()
        self.assertEqual(db_probe['status'], HealthStatus.HEALTHY)
        self.assertGreater(db_probe['latency_ms'], 0.0)

        tf_probe = SystemHealthProbeService.probe_forecasting_engine()
        self.assertEqual(tf_probe['status'], HealthStatus.HEALTHY)

        ollama_probe = SystemHealthProbeService.probe_ollama()
        # In sandbox environment without external port access, Ollama probe returns UNKNOWN with fallback active
        self.assertIn(ollama_probe['status'], [HealthStatus.HEALTHY, HealthStatus.UNKNOWN])
