import uuid
import logging
from decimal import Decimal
from typing import Optional, Dict
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import PurchaseOrder, PurchaseOrderItem, ProcurementPolicy, POStatus, POCategory
from apps.suppliers.models import Supplier, SupplierProduct, SupplierStatus
from apps.suppliers.services import SupplierEvaluationService
from apps.inventory.models import Product, Warehouse
from apps.forecasting.services import DynamicROPDecisionEngine
from apps.audit.models import AuditLog

logger = logging.getLogger('scale_core.procurement')


class AutonomousProcurementService:
    """
    Autonomous Procurement Engine & Policy Gatekeeper.
    Part 12 of the Master Specification.
    Enforces Category B automated dispatch vs Category C supervisor escalation.
    """

    @classmethod
    @transaction.atomic
    def generate_replenishment_order(
        cls,
        product: Product,
        warehouse: Warehouse,
        order_quantity: Optional[Decimal] = None,
        ai_justification: str = '',
        actor=None
    ) -> PurchaseOrder:
        """
        Evaluates supplier options, computes order value, applies policy gate,
        and generates an autonomous or approval-queued purchase order.
        """
        # 1. Determine recommended quantity if not passed explicitly
        if not order_quantity or order_quantity <= Decimal('0.00'):
            rop_calc = DynamicROPDecisionEngine.calculate_rop_and_safety_stock(product, warehouse)
            order_quantity = rop_calc['recommended_order_quantity']

        if order_quantity <= Decimal('0.00'):
            raise ValidationError(f"No replenishment quantity required for {product.sku}.")

        # 2. Multi-factor supplier evaluation and ranking
        ranked_suppliers = SupplierEvaluationService.evaluate_and_rank_suppliers(product)
        if not ranked_suppliers:
            raise ValidationError(f"No approved active suppliers available for product {product.sku}.")

        best_supplier_info = ranked_suppliers[0]
        supplier = Supplier.objects.get(id=best_supplier_info['supplier_id'])
        unit_price = best_supplier_info['contracted_price']
        lead_time = best_supplier_info['lead_time_days']

        total_value = order_quantity * unit_price

        # 3. Policy Gatekeeper Evaluation (Part 12.3)
        policy = ProcurementPolicy.objects.filter(is_active=True).first()
        auto_ceiling = policy.auto_dispatch_max_value if policy else Decimal('5000.00')
        min_reliability = policy.min_supplier_reliability_score if policy else Decimal('80.00')

        is_eligible_for_auto_dispatch = (
            total_value <= auto_ceiling and
            supplier.composite_score >= min_reliability and
            supplier.status == SupplierStatus.ACTIVE
        )

        category = POCategory.CATEGORY_B if is_eligible_for_auto_dispatch else POCategory.CATEGORY_C
        initial_status = POStatus.DISPATCHED if is_eligible_for_auto_dispatch else POStatus.AWAITING_APPROVAL

        # Generate unique PO number
        today_str = timezone.now().strftime('%Y-%m')
        count = PurchaseOrder.objects.filter(created_at__year=timezone.now().year).count() + 1
        po_number = f"PO-{today_str}-{count:04d}"

        expected_delivery = timezone.now().date() + timezone.timedelta(days=lead_time)

        po = PurchaseOrder.objects.create(
            po_number=po_number,
            supplier=supplier,
            warehouse=warehouse,
            total_amount=total_value,
            status=initial_status,
            category=category,
            generated_by_system=True,
            ai_justification=ai_justification or (
                f"Autonomous replenishment triggered for {product.sku}. "
                f"Selected vendor {supplier.legal_name} (Score: {supplier.composite_score:.1f}). "
                f"Order value: ${total_value:,.2f}."
            ),
            expected_delivery_date=expected_delivery,
            dispatched_at=timezone.now() if is_eligible_for_auto_dispatch else None
        )

        PurchaseOrderItem.objects.create(
            purchase_order=po,
            product=product,
            quantity=order_quantity,
            unit_price=unit_price
        )

        # Update incoming stock on inventory balance if dispatched
        if is_eligible_for_auto_dispatch:
            bal = product.balances.filter(warehouse=warehouse).first()
            if bal:
                bal.incoming_stock += order_quantity
                bal.save(update_fields=['incoming_stock', 'updated_at'])

        # Record in Immutable Audit Ledger
        AuditLog.record_event(
            event_type='PURCHASE_ORDER_GENERATED',
            entity_type='PURCHASE_ORDER',
            entity_id=str(po.id),
            actor=actor,
            state_after={
                'po_number': po.po_number,
                'supplier': supplier.code,
                'total_amount': str(po.total_amount),
                'category': category,
                'status': initial_status
            }
        )

        return po

    @classmethod
    @transaction.atomic
    def approve_purchase_order(cls, po: PurchaseOrder, supervisor, notes: str = '') -> PurchaseOrder:
        """
        Supervisor gateway: Authorizes and dispatches a Category C high-risk purchase order.
        """
        if not supervisor or not getattr(supervisor, 'is_manager', False):
            raise ValidationError("Authorization failed: Only System Supervisors (Managers) can approve POs.")

        if po.status != POStatus.AWAITING_APPROVAL:
            raise ValidationError(f"Cannot approve PO in status '{po.get_status_display()}'.")

        po.status = POStatus.DISPATCHED
        po.approved_by = supervisor
        po.approved_at = timezone.now()
        po.dispatched_at = timezone.now()
        if notes:
            po.ai_justification += f"\n[Supervisor Note]: {notes}"
        po.save()

        # Update incoming stock on inventory balances for each item
        for item in po.items.select_related('product'):
            bal = item.product.balances.filter(warehouse=po.warehouse).first()
            if bal:
                bal.incoming_stock += item.quantity
                bal.save(update_fields=['incoming_stock', 'updated_at'])

        # Record in Immutable Audit Ledger
        AuditLog.record_event(
            event_type='PURCHASE_ORDER_APPROVED',
            entity_type='PURCHASE_ORDER',
            entity_id=str(po.id),
            actor=supervisor,
            state_before={'status': POStatus.AWAITING_APPROVAL},
            state_after={
                'status': POStatus.DISPATCHED,
                'po_number': po.po_number,
                'approved_by': supervisor.username,
                'dispatched_at': po.dispatched_at.isoformat()
            }
        )

        return po

    @classmethod
    @transaction.atomic
    def reject_purchase_order(cls, po: PurchaseOrder, supervisor, reason: str = '') -> PurchaseOrder:
        """
        Supervisor rejects purchase order draft.
        """
        if not supervisor or not getattr(supervisor, 'is_manager', False):
            raise ValidationError("Authorization failed: Only Managers can reject purchase orders.")

        po.status = POStatus.CANCELLED
        po.ai_justification += f"\n[Supervisor Rejection Reason]: {reason}"
        po.save(update_fields=['status', 'ai_justification'])

        AuditLog.record_event(
            event_type='PURCHASE_ORDER_REJECTED',
            entity_type='PURCHASE_ORDER',
            entity_id=str(po.id),
            actor=supervisor,
            state_after={'status': POStatus.CANCELLED, 'reason': reason}
        )
        return po
