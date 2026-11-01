from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import SCALEUserRole
from apps.inventory.models import Warehouse, ProductCategory, Product, InventoryBalance
from apps.suppliers.models import Supplier, SupplierProduct, SupplierStatus
from apps.procurement.models import ProcurementPolicy, PurchaseOrder, POStatus
from apps.intelligence.services import OperationalAIAdvisor, LocalOllamaClient
from apps.automation.models import WorkflowStatus
from apps.automation.services import AutonomousWorkflowOrchestrator
from apps.audit.models import AuditLog

User = get_user_model()


class AutomationAndAITests(TestCase):
    """
    Test suite for Phase 8: Local AI Operations & Phase 9: Autonomous Workflow Orchestration.
    """

    def setUp(self):
        self.manager = User.objects.create_user(username='mgr_auto', password='Password123!', role=SCALEUserRole.MANAGER)

        self.wh = Warehouse.objects.create(code='WH-AUTO-01', name='Automation Fulfillment Hub')
        self.cat = ProductCategory.objects.create(code='CAT-AUTO', name='Electronics')
        self.product = Product.objects.create(
            sku='SKU-AUTO-01',
            name='Autonomous Robotic Drive',
            category=self.cat,
            unit_cost=Decimal('100.00'),
            unit_price=Decimal('160.00'),
            reorder_point=Decimal('200.00'),
            safety_stock=Decimal('60.00'),
            minimum_order_qty=Decimal('40.00'),
            order_multiple=Decimal('10.00'),
            lead_time_days_avg=Decimal('7.00'),
            lead_time_days_std=Decimal('1.00')
        )
        self.balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.wh,
            on_hand_stock=Decimal('40.00'),  # Critical stockout condition: 40 < 200
            reserved_stock=Decimal('0.00'),
            incoming_stock=Decimal('0.00')
        )

        self.supplier = Supplier.objects.create(
            code='SUPP-AUTO-01',
            legal_name='Apex Robotics Supply',
            reliability_score=Decimal('98.00'),
            quality_score=Decimal('98.00'),
            lead_time_compliance_rate=Decimal('98.00'),
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
            policy_name='Standard Operations Policy',
            auto_dispatch_max_value=Decimal('5000.00'),
            require_approval_above_value=Decimal('5000.00')
        )

    def test_local_ai_query_context_retrieval(self):
        """Verify context-aware operational retrieval for critical stockouts (Part 18)."""
        result = OperationalAIAdvisor.answer_operational_query("Which products are at critical stockout risk?", user=self.manager)
        self.assertIn('critical_stockouts', result['context_data'])
        self.assertIsNotNone(result['answer'])
        self.assertIn('SKU-AUTO-01', str(result['context_data']))

    def test_nightly_autonomous_pipeline_lifecycle(self):
        """Verify the 8-stage 02:00 AM autonomous pipeline runs end to end (Part 22)."""
        execution = AutonomousWorkflowOrchestrator.execute_nightly_autonomous_pipeline(actor=self.manager)

        self.assertIn(execution.status, [WorkflowStatus.COMPLETED, WorkflowStatus.AWAITING_APPROVAL])
        stages = execution.execution_context.get('stages_completed', [])

        self.assertTrue(any('ETL_VERIFIED' in s for s in stages))
        self.assertTrue(any('FORECASTING_COMPLETED' in s for s in stages))
        self.assertTrue(any('ROP_RECALIBRATED' in s for s in stages))
        self.assertTrue(any('PROCUREMENT_EVALUATED' in s for s in stages))
        self.assertTrue(any('ABC_XYZ_UPDATED' in s for s in stages))
        self.assertTrue(any('FINANCIAL_SNAPSHOT' in s for s in stages))
        self.assertTrue(any('AUDIT_VERIFIED' in s for s in stages))

    def test_automation_telemetry_metrics(self):
        """Verify HIR and Automation Rate calculation (Part 16.3)."""
        telemetry = AutonomousWorkflowOrchestrator.get_automation_telemetry()
        self.assertIn('automation_rate_pct', telemetry)
        self.assertIn('human_intervention_rate_pct', telemetry)
        self.assertGreaterEqual(telemetry['automation_rate_pct'], 0.0)
        self.assertLessEqual(telemetry['automation_rate_pct'], 100.0)
