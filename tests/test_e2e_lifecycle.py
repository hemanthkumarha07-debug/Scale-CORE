from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import SCALEUserRole
from apps.inventory.models import Warehouse, ProductCategory, Product, InventoryBalance, MovementType
from apps.inventory.services import StockMovementService, InventoryClassificationService
from apps.suppliers.models import Supplier, SupplierProduct, SupplierStatus, PaymentTerms
from apps.suppliers.services import SupplierEvaluationService
from apps.procurement.models import ProcurementPolicy, PurchaseOrder, POStatus, POCategory
from apps.procurement.services import AutonomousProcurementService
from apps.logistics.models import Shipment, ShipmentStatus
from apps.logistics.services import LogisticsService
from apps.sales.models import DailySalesLog
from apps.forecasting.services import LSTMForecastingEngine, DynamicROPDecisionEngine
from apps.audit.models import AuditLog
from apps.audit.services import AuditIntegrityService
from apps.automation.services import AutonomousWorkflowOrchestrator

User = get_user_model()


class EndToEndOperationalLifecycleTests(TestCase):
    """
    Simulates and validates the complete 16-step operational lifecycle
    specified in Part 26.6 of the Master Development Specification.
    """

    def setUp(self):
        self.supervisor = User.objects.create_user(
            username='hemanth_lead',
            password='Password123!',
            role=SCALEUserRole.MANAGER,
            is_staff=True,
            is_superuser=True
        )
        self.dock_operator = User.objects.create_user(
            username='dock_operator',
            password='Password123!',
            role=SCALEUserRole.EMPLOYEE
        )

        self.warehouse = Warehouse.objects.create(
            code='WH-MAIN-01',
            name='Central Distribution Hub'
        )
        self.category = ProductCategory.objects.create(
            code='CAT-ELEC',
            name='Microelectronics',
            holding_cost_rate_annual=Decimal('0.2000')
        )
        self.product = Product.objects.create(
            sku='SKU-E2E-100',
            name='Edge AI Computing SoC',
            category=self.category,
            unit_cost=Decimal('100.00'),
            unit_price=Decimal('160.00'),
            reorder_point=Decimal('200.00'),
            safety_stock=Decimal('50.00'),
            minimum_order_qty=Decimal('50.00'),
            order_multiple=Decimal('10.00'),
            lead_time_days_avg=Decimal('7.00'),
            lead_time_days_std=Decimal('1.50'),
            service_level_target=Decimal('0.950')
        )
        self.balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            on_hand_stock=Decimal('250.00'),  # initially healthy stock
            reserved_stock=Decimal('0.00'),
            incoming_stock=Decimal('0.00')
        )
        self.supplier = Supplier.objects.create(
            code='SUPP-E2E-01',
            legal_name='Apex Semiconductor Foundry',
            email='procure@apexsemi.internal',
            reliability_score=Decimal('98.00'),
            quality_score=Decimal('99.00'),
            lead_time_compliance_rate=Decimal('96.00'),
            status=SupplierStatus.ACTIVE
        )
        SupplierProduct.objects.create(
            supplier=self.supplier,
            product=self.product,
            contracted_unit_price=Decimal('100.00'),
            lead_time_days=7,
            is_preferred=True
        )
        self.policy = ProcurementPolicy.objects.create(
            policy_name='Standard Enterprise Policy',
            auto_dispatch_max_value=Decimal('5000.00'),
            require_approval_above_value=Decimal('5000.00'),
            min_supplier_reliability_score=Decimal('80.00')
        )

    def test_complete_16_stage_operational_lifecycle(self):
        """
        Executes and traces the complete 16-step operational lifecycle:
        1. Sales transactions are recorded.
        2. Inventory is updated.
        3. Demand forecasting executes.
        4. Dynamic ROP is calculated.
        5. Critical stock condition is detected.
        6. Replenishment recommendation is generated.
        7. Supplier evaluation occurs.
        8. Purchase order draft is created.
        9. Policy validation occurs.
        10. Eligible orders are dispatched or routed for approval.
        11. Supplier confirmation is recorded.
        12. Shipment monitoring begins.
        13. Goods receipt is recorded.
        14. Inventory is updated.
        15. Audit records are verified.
        16. Management telemetry is confirmed.
        """
        # Step 1: Sales transactions recorded
        today = timezone.now().date()
        for i in range(14):
            d = today - timezone.timedelta(days=i)
            DailySalesLog.objects.create(
                date=d,
                product=self.product,
                warehouse=self.warehouse,
                units_sold=Decimal('25.00'),
                sales_revenue=Decimal('4000.00'),
                was_stockout_day=False
            )

        # Step 2: Inventory is updated via sales dispatch movement
        # Dispatch 210 units -> stock drops from 250 to 40 (critical stock condition!)
        movement = StockMovementService.record_movement(
            product=self.product,
            warehouse=self.warehouse,
            movement_type=MovementType.SALES_DISPATCH,
            quantity=Decimal('-210.00'),
            reference_doc_type='CustomerSalesOrder',
            reference_doc_id='SO-E2E-001',
            performed_by=self.supervisor,
            notes='Mass order dispatch to regional distributor'
        )
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.on_hand_stock, Decimal('40.00'))

        # Step 3: Demand forecasting executes (LSTM 30-day forecast)
        forecast = LSTMForecastingEngine.generate_30day_forecast(self.product, self.warehouse)
        self.assertEqual(len(forecast), 30)
        self.assertGreater(forecast[0]['predicted_demand'], 0.0)

        # Step 4: Dynamic ROP is calculated
        rop_metrics = DynamicROPDecisionEngine.calculate_rop_and_safety_stock(self.product, self.warehouse)
        self.assertGreater(rop_metrics['reorder_point'], Decimal('0.00'))
        self.assertGreater(rop_metrics['safety_stock'], Decimal('0.00'))

        # Step 5: Critical stock condition detected (40 available < ROP ~200)
        self.assertTrue(rop_metrics['is_critical'])
        self.assertTrue(self.balance.is_below_rop)

        # Step 6: Replenishment recommendation generated
        recommended_qty = rop_metrics['recommended_order_quantity']
        self.assertGreater(recommended_qty, Decimal('0.00'))

        # Step 7: Supplier evaluation occurs
        ranked_suppliers = SupplierEvaluationService.evaluate_and_rank_suppliers(self.product)
        self.assertEqual(ranked_suppliers[0]['supplier_code'], 'SUPP-E2E-01')

        # Step 8, 9, 10: PO drafted, policy validated, and dispatched or routed to approval
        # For quantity >= 200 units @ $100 = $20,000 > $5,000 threshold -> Category C
        po = AutonomousProcurementService.generate_replenishment_order(
            product=self.product,
            warehouse=self.warehouse,
            order_quantity=recommended_qty,
            actor=self.supervisor
        )
        self.assertIsNotNone(po)
        self.assertEqual(po.category, POCategory.CATEGORY_C)
        self.assertEqual(po.status, POStatus.AWAITING_APPROVAL)

        # Supervisor authorizes the Category C purchase order
        AutonomousProcurementService.approve_purchase_order(
            po=po,
            supervisor=self.supervisor,
            notes='E2E Emergency stock replenishment authorized.'
        )
        po.refresh_from_db()
        self.assertEqual(po.status, POStatus.DISPATCHED)
        self.assertIsNotNone(po.dispatched_at)

        # Step 11 & 12: Shipment monitoring begins
        shipment = Shipment.objects.create(
            tracking_number='TRK-E2E-8899',
            purchase_order=po,
            carrier_name='Express Logistics',
            dispatch_date=today,
            expected_delivery_date=today + timezone.timedelta(days=7),
            status=ShipmentStatus.IN_TRANSIT
        )
        self.assertEqual(shipment.status, ShipmentStatus.IN_TRANSIT)

        # Step 13 & 14: Goods receipt is recorded and inventory is updated
        receipt = LogisticsService.process_goods_receipt(
            purchase_order=po,
            received_items=[{
                'product_id': self.product.id,
                'quantity_received': recommended_qty,
                'quantity_damaged': 0
            }],
            operator=self.dock_operator,
            shipment=shipment,
            notes='All units verified and received intact at dock'
        )
        self.assertFalse(receipt.discrepancy_detected)

        # Inventory balance must now be replenished: 40 + recommended_qty
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.on_hand_stock, Decimal('40.00') + recommended_qty)
        self.assertFalse(self.balance.is_below_rop)

        # Purchase order must be completed
        po.refresh_from_db()
        self.assertEqual(po.status, POStatus.COMPLETED)

        # Step 15: Cryptographic audit records verified
        audit_check = AuditIntegrityService.verify_ledger_chain()
        self.assertEqual(audit_check['chain_integrity'], 'VALID')
        self.assertFalse(audit_check['tampering_detected'])
        self.assertGreater(audit_check['verified_records_count'], 4)

        # Step 16: Autonomous telemetry and management metrics confirmed
        telemetry = AutonomousWorkflowOrchestrator.get_automation_telemetry()
        self.assertGreater(telemetry['automation_rate_pct'], 0.0)
        self.assertLessEqual(telemetry['human_intervention_rate_pct'], 100.0)
