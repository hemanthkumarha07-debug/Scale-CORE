from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.accounts.models import SCALEUserRole
from apps.inventory.models import Warehouse, ProductCategory, Product, InventoryBalance, ABCClass, XYZClass, ProductStatus
from apps.suppliers.models import Supplier, SupplierProduct, SupplierStatus, PaymentTerms
from apps.procurement.models import ProcurementPolicy, PurchaseOrder, PurchaseOrderItem, POStatus, POCategory
from apps.finance.models import FinancialSnapshot
from apps.automation.models import AutomationWorkflow, WorkflowExecution, WorkflowStatus, ExecutionCategory
from apps.audit.models import AuditLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial enterprise foundation data for SCALE.Core'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Seeding SCALE.Core Enterprise Foundation ---"))

        # 1. Accounts
        supervisor, created = User.objects.get_or_create(
            username='hemanth.supervisor',
            defaults={
                'email': 'hemanth@scale.internal',
                'first_name': 'Hemanth',
                'last_name': 'Kumar H A',
                'role': SCALEUserRole.MANAGER,
                'is_staff': True,
                'is_superuser': True,
                'department': 'Operations Leadership'
            }
        )
        if created:
            supervisor.set_password('Password123!')
            supervisor.save()
            self.stdout.write(f"Created Supervisor User: {supervisor.username}")

        operator, created = User.objects.get_or_create(
            username='operator.warehouse',
            defaults={
                'email': 'operator@scale.internal',
                'first_name': 'Dock',
                'last_name': 'Operator',
                'role': SCALEUserRole.EMPLOYEE,
                'department': 'Warehouse Logistics'
            }
        )
        if created:
            operator.set_password('Password123!')
            operator.save()
            self.stdout.write(f"Created Operational User: {operator.username}")

        # 2. Warehouses
        wh1, _ = Warehouse.objects.get_or_create(
            code='WH-CENTRAL-01',
            defaults={'name': 'Central Fulfillment Hub', 'address': 'Sector 18, Logistics Park', 'city': 'Mumbai', 'total_capacity_sqft': Decimal('120000.00')}
        )
        wh2, _ = Warehouse.objects.get_or_create(
            code='WH-NORTH-01',
            defaults={'name': 'Northern Distribution Center', 'address': 'Plot 44, Express Corridor', 'city': 'Delhi', 'total_capacity_sqft': Decimal('85000.00')}
        )
        wh3, _ = Warehouse.objects.get_or_create(
            code='WH-SOUTH-01',
            defaults={'name': 'Southern Regional Hub', 'address': 'Electronics City Phase 2', 'city': 'Bangalore', 'total_capacity_sqft': Decimal('95000.00')}
        )

        # 3. Product Categories
        cat_elec, _ = ProductCategory.objects.get_or_create(
            code='CAT-ELEC',
            defaults={'name': 'Electronics & Microcontrollers', 'holding_cost_rate_annual': Decimal('0.2000')}
        )
        cat_mech, _ = ProductCategory.objects.get_or_create(
            code='CAT-MECH',
            defaults={'name': 'Mechanical & Actuation', 'holding_cost_rate_annual': Decimal('0.1500')}
        )
        cat_power, _ = ProductCategory.objects.get_or_create(
            code='CAT-POWR',
            defaults={'name': 'Power Systems & Energy', 'holding_cost_rate_annual': Decimal('0.1800')}
        )

        # 4. Products Master
        p1, _ = Product.objects.get_or_create(
            sku='SKU-ELEC-4091',
            defaults={
                'name': 'Microcontroller MCU-32 Dual Core',
                'category': cat_elec,
                'unit_cost': Decimal('24.5000'),
                'unit_price': Decimal('38.0000'),
                'abc_class': ABCClass.A,
                'xyz_class': XYZClass.X,
                'reorder_point': Decimal('380.00'),
                'safety_stock': Decimal('120.00'),
                'minimum_order_qty': Decimal('100.00'),
                'order_multiple': Decimal('50.00'),
                'lead_time_days_avg': Decimal('7.00'),
                'lead_time_days_std': Decimal('1.50'),
                'service_level_target': Decimal('0.950'),
                'status': ProductStatus.ACTIVE
            }
        )

        p2, _ = Product.objects.get_or_create(
            sku='SKU-MECH-1022',
            defaults={
                'name': 'Industrial Hydraulic Actuator 24V',
                'category': cat_mech,
                'unit_cost': Decimal('115.0000'),
                'unit_price': Decimal('180.0000'),
                'abc_class': ABCClass.A,
                'xyz_class': XYZClass.Y,
                'reorder_point': Decimal('120.00'),
                'safety_stock': Decimal('40.00'),
                'minimum_order_qty': Decimal('20.00'),
                'order_multiple': Decimal('10.00'),
                'lead_time_days_avg': Decimal('14.00'),
                'lead_time_days_std': Decimal('3.00'),
                'service_level_target': Decimal('0.950'),
                'status': ProductStatus.ACTIVE
            }
        )

        p3, _ = Product.objects.get_or_create(
            sku='SKU-POWR-8831',
            defaults={
                'name': 'Lithium Power Module 48V 10Ah',
                'category': cat_power,
                'unit_cost': Decimal('320.0000'),
                'unit_price': Decimal('495.0000'),
                'abc_class': ABCClass.A,
                'xyz_class': XYZClass.Z,
                'reorder_point': Decimal('210.00'),
                'safety_stock': Decimal('70.00'),
                'minimum_order_qty': Decimal('15.00'),
                'order_multiple': Decimal('5.00'),
                'lead_time_days_avg': Decimal('10.00'),
                'lead_time_days_std': Decimal('2.00'),
                'service_level_target': Decimal('0.950'),
                'status': ProductStatus.ACTIVE
            }
        )

        # 5. Inventory Balances (Critical condition simulated on SKU-ELEC-4091)
        b1, _ = InventoryBalance.objects.get_or_create(
            product=p1,
            warehouse=wh1,
            defaults={'on_hand_stock': Decimal('42.00'), 'reserved_stock': Decimal('0.00'), 'incoming_stock': Decimal('0.00')}
        )
        b2, _ = InventoryBalance.objects.get_or_create(
            product=p2,
            warehouse=wh1,
            defaults={'on_hand_stock': Decimal('18.00'), 'reserved_stock': Decimal('0.00'), 'incoming_stock': Decimal('0.00')}
        )
        b3, _ = InventoryBalance.objects.get_or_create(
            product=p3,
            warehouse=wh1,
            defaults={'on_hand_stock': Decimal('65.00'), 'reserved_stock': Decimal('0.00'), 'incoming_stock': Decimal('0.00')}
        )

        # 6. Verified Suppliers
        s1, _ = Supplier.objects.get_or_create(
            code='SUPP-ALPHA-01',
            defaults={
                'legal_name': 'Alpha Component Co',
                'contact_person': 'David Vance',
                'email': 'dvance@alphacomponents.com',
                'phone': '+91-9876543210',
                'address': 'Industrial Area Phase 1, Bangalore',
                'payment_terms': PaymentTerms.NET_30,
                'reliability_score': Decimal('96.50'),
                'quality_score': Decimal('98.00'),
                'lead_time_compliance_rate': Decimal('95.00'),
                'status': SupplierStatus.ACTIVE
            }
        )

        s2, _ = Supplier.objects.get_or_create(
            code='SUPP-BETA-02',
            defaults={
                'legal_name': 'Beta Precision Hydraulics',
                'contact_person': 'Anita Sharma',
                'email': 'asharma@betahydraulics.com',
                'phone': '+91-9876543211',
                'address': 'MIDC Logistics Zone, Pune',
                'payment_terms': PaymentTerms.NET_30,
                'reliability_score': Decimal('92.00'),
                'quality_score': Decimal('94.00'),
                'lead_time_compliance_rate': Decimal('90.00'),
                'status': SupplierStatus.ACTIVE
            }
        )

        # Link Supplier Products
        SupplierProduct.objects.get_or_create(
            supplier=s1,
            product=p1,
            defaults={'contracted_unit_price': Decimal('24.5000'), 'lead_time_days': 7, 'is_preferred': True}
        )
        SupplierProduct.objects.get_or_create(
            supplier=s2,
            product=p2,
            defaults={'contracted_unit_price': Decimal('115.0000'), 'lead_time_days': 14, 'is_preferred': True}
        )

        # 7. Procurement Policy
        policy, _ = ProcurementPolicy.objects.get_or_create(
            policy_name='Standard Enterprise Operations Policy',
            defaults={
                'auto_dispatch_max_value': Decimal('5000.00'),
                'require_approval_above_value': Decimal('5000.00'),
                'max_supplier_price_variance_pct': Decimal('15.00'),
                'min_supplier_reliability_score': Decimal('80.00'),
                'is_active': True
            }
        )

        # 8. Pending Category C Purchase Order (Awaiting Approval)
        po, created = PurchaseOrder.objects.get_or_create(
            po_number='PO-2026-11-0001',
            defaults={
                'supplier': s1,
                'warehouse': wh1,
                'total_amount': Decimal('11025.00'),
                'status': POStatus.AWAITING_APPROVAL,
                'category': POCategory.CATEGORY_C,
                'generated_by_system': True,
                'ai_justification': 'Emergency replenishment for SKU-ELEC-4091. Stock will deplete in 3.8 days. Order value ($11,025.00) exceeds $5,000 threshold.',
                'expected_delivery_date': timezone.now().date() + timezone.timedelta(days=7)
            }
        )
        if created:
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                product=p1,
                quantity=Decimal('450.00'),
                unit_price=Decimal('24.5000')
            )

        # 9. Initial Financial Snapshot
        FinancialSnapshot.objects.get_or_create(
            snapshot_date=timezone.now().date(),
            defaults={
                'total_inventory_valuation': Decimal('842500.00'),
                'total_capital_at_risk': Decimal('38210.00'),
                'total_excess_inventory_value': Decimal('38210.00'),
                'annual_holding_cost_projected': Decimal('7642.00'),
                'total_pending_po_commitments': Decimal('11025.00')
            }
        )

        # 10. Automation Workflow Definitions
        wf1, _ = AutomationWorkflow.objects.get_or_create(
            name='Autonomous Nightly Cycle (02:00 AM)',
            defaults={'workflow_type': 'NIGHTLY_PIPELINE', 'execution_category': ExecutionCategory.CATEGORY_A}
        )
        wf2, _ = AutomationWorkflow.objects.get_or_create(
            name='Purchase Order Policy Gate Evaluation',
            defaults={'workflow_type': 'PO_DISPATCH_GATE', 'execution_category': ExecutionCategory.CATEGORY_B}
        )

        # Initial Execution Record
        WorkflowExecution.objects.get_or_create(
            workflow=wf1,
            idempotency_key='seed-nightly-cycle-0001',
            defaults={
                'status': WorkflowStatus.COMPLETED,
                'completed_at': timezone.now(),
                'execution_context': {'stages_completed': ['ETL', 'LSTM_INFERENCE', 'DYNAMIC_ROP', 'RECONCILIATION']}
            }
        )

        # 11. Initial Cryptographic Audit Record
        AuditLog.record_event(
            event_type='SYSTEM_FOUNDATION_INITIALIZED',
            entity_type='SCALE_CORE_SYSTEM',
            entity_id='GENESIS_01',
            actor=supervisor,
            state_after={'status': 'OPERATIONAL', 'version': '1.0.0-rc1', 'philosophy': 'One human supervises. SCALE.Core operates.'}
        )

        self.stdout.write(self.style.SUCCESS("--- Seeding Completed Successfully! ---"))
