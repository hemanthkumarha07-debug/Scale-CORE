import uuid
import logging
from decimal import Decimal
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, F, Avg, StdDev
from django.core.exceptions import ValidationError

from .models import (
    Product, Warehouse, InventoryBalance, InventoryMovement,
    MovementType, StockReconciliation, StockReconciliationItem,
    ReconciliationStatus, ABCClass, XYZClass
)
from apps.sales.models import DailySalesLog
from apps.audit.models import AuditLog

logger = logging.getLogger('scale_core.inventory')


class StockMovementService:
    """
    Transactional stock movement engine.
    Ensures that every physical stock modification updates the master balance
    and leaves an auditable transaction footprint.
    """
    @classmethod
    @transaction.atomic
    def record_movement(
        cls,
        product: Product,
        warehouse: Warehouse,
        movement_type: str,
        quantity: Decimal,
        reference_doc_type: str = '',
        reference_doc_id: str = '',
        performed_by=None,
        notes: str = ''
    ) -> InventoryMovement:
        """
        Record a stock movement with pessimistic row locking.
        Quantity: positive for inbound (e.g. goods receipt), negative for outbound (e.g. dispatch).
        """
        quantity = Decimal(str(quantity))
        if quantity == Decimal('0.00'):
            raise ValidationError("Movement quantity cannot be zero.")

        # Pessimistic locking on balance row
        balance, _ = InventoryBalance.objects.select_for_update().get_or_create(
            product=product,
            warehouse=warehouse,
            defaults={
                'on_hand_stock': Decimal('0.00'),
                'reserved_stock': Decimal('0.00'),
                'incoming_stock': Decimal('0.00'),
                'damaged_stock': Decimal('0.00')
            }
        )

        balance_before = balance.on_hand_stock
        balance_after = balance_before + quantity

        if balance_after < Decimal('0.00') and movement_type != MovementType.COUNT_ADJUSTMENT:
            raise ValidationError(
                f"Insufficient physical stock for {product.sku} at {warehouse.code}. "
                f"Available on-hand: {balance_before}, requested reduction: {abs(quantity)}"
            )

        # Update balance
        balance.on_hand_stock = max(Decimal('0.00'), balance_after)
        balance.save(update_fields=['on_hand_stock', 'updated_at'])

        # Generate unique transaction number
        tx_number = f"TX-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        movement = InventoryMovement.objects.create(
            transaction_number=tx_number,
            product=product,
            warehouse=warehouse,
            movement_type=movement_type,
            quantity=quantity,
            balance_before=balance_before,
            balance_after=balance.on_hand_stock,
            reference_doc_type=reference_doc_type,
            reference_doc_id=reference_doc_id,
            performed_by=performed_by,
            notes=notes
        )

        # Record in Immutable Audit Ledger
        AuditLog.record_event(
            event_type='INVENTORY_MOVEMENT',
            entity_type='INVENTORY_BALANCE',
            entity_id=str(balance.id),
            actor=performed_by,
            state_before={'on_hand_stock': str(balance_before)},
            state_after={
                'on_hand_stock': str(balance.on_hand_stock),
                'movement_type': movement_type,
                'quantity': str(quantity),
                'tx_number': tx_number
            }
        )

        return movement


class InventoryClassificationService:
    """
    Deterministic ABC and XYZ Classification Engine.
    Part 8.4 of the Master Specification.
    - ABC: Pareto 80/20 analysis based on cumulative sales revenue.
    - XYZ: Demand variability classification based on Coefficient of Variation (CV).
    """
    @classmethod
    def run_abc_analysis(cls) -> Dict[str, int]:
        """
        Classifies all active products into ABC classes based on revenue.
        Class A: Top 80% cumulative revenue
        Class B: Next 15% (80% - 95%)
        Class C: Bottom 5% (95% - 100%)
        """
        # Calculate revenue per product from DailySalesLog
        sales_by_product = DailySalesLog.objects.values('product_id').annotate(
            total_rev=Sum('sales_revenue')
        ).order_by('-total_rev')

        total_system_rev = DailySalesLog.objects.aggregate(t=Sum('sales_revenue'))['t'] or Decimal('0.00')

        counts = {'A': 0, 'B': 0, 'C': 0}

        if total_system_rev == Decimal('0.00'):
            # Fallback based on unit_price * average stock if no sales history
            products = Product.objects.all().order_by('-unit_price')
            total_prods = products.count()
            for idx, p in enumerate(products):
                pct = (idx + 1) / max(1, total_prods)
                if pct <= 0.20:
                    p.abc_class = ABCClass.A
                    counts['A'] += 1
                elif pct <= 0.50:
                    p.abc_class = ABCClass.B
                    counts['B'] += 1
                else:
                    p.abc_class = ABCClass.C
                    counts['C'] += 1
                p.save(update_fields=['abc_class'])
            return counts

        cum_rev = Decimal('0.00')
        for item in sales_by_product:
            cum_rev += (item['total_rev'] or Decimal('0.00'))
            cum_pct = cum_rev / total_system_rev
            prod_id = item['product_id']

            if cum_pct <= Decimal('0.80'):
                cls_val = ABCClass.A
                counts['A'] += 1
            elif cum_pct <= Decimal('0.95'):
                cls_val = ABCClass.B
                counts['B'] += 1
            else:
                cls_val = ABCClass.C
                counts['C'] += 1

            Product.objects.filter(id=prod_id).update(abc_class=cls_val)

        return counts

    @classmethod
    def run_xyz_analysis(cls) -> Dict[str, int]:
        """
        Classifies products into XYZ demand variability based on CV = sigma / mu.
        X (Low variability / constant demand): CV <= 0.10
        Y (Moderate variability): 0.10 < CV <= 0.25
        Z (High variability / irregular): CV > 0.25
        """
        counts = {'X': 0, 'Y': 0, 'Z': 0}
        products = Product.objects.all()

        for p in products:
            stats = DailySalesLog.objects.filter(product=p).aggregate(
                mean_demand=Avg('units_sold'),
                std_demand=StdDev('units_sold')
            )
            mean_d = stats['mean_demand']
            std_d = stats['std_demand']

            if mean_d and mean_d > 0 and std_d is not None:
                cv = float(std_d) / float(mean_d)
                if cv <= 0.10:
                    p.xyz_class = XYZClass.X
                    counts['X'] += 1
                elif cv <= 0.25:
                    p.xyz_class = XYZClass.Y
                    counts['Y'] += 1
                else:
                    p.xyz_class = XYZClass.Z
                    counts['Z'] += 1
            else:
                # Default to Y if insufficient observations
                p.xyz_class = XYZClass.Y
                counts['Y'] += 1

            p.save(update_fields=['xyz_class'])

        return counts


class StockReconciliationService:
    """
    Workflow for physical inventory count audit and supervisor-approved adjustments.
    Part 8.5 of the Master Specification.
    """
    @classmethod
    def create_batch(cls, warehouse: Warehouse, assigned_to) -> StockReconciliation:
        rec_number = f"REC-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        reconciliation = StockReconciliation.objects.create(
            reconciliation_number=rec_number,
            warehouse=warehouse,
            assigned_to=assigned_to,
            status=ReconciliationStatus.DRAFT
        )

        # Pre-populate all active inventory balances for counting
        balances = InventoryBalance.objects.filter(warehouse=warehouse).select_related('product')
        for b in balances:
            StockReconciliationItem.objects.create(
                reconciliation=reconciliation,
                product=b.product,
                system_quantity=b.on_hand_stock,
                physical_quantity=b.on_hand_stock,  # initial placeholder
                discrepancy_quantity=Decimal('0.00'),
                discrepancy_cost=Decimal('0.00')
            )

        return reconciliation

    @classmethod
    @transaction.atomic
    def approve_reconciliation(cls, reconciliation: StockReconciliation, supervisor) -> StockReconciliation:
        """
        Supervisor approves discrepancy adjustments.
        Automatically updates on-hand balances, generates stock movements, and records audit logs.
        """
        if reconciliation.status == ReconciliationStatus.APPROVED:
            raise ValidationError("This reconciliation batch is already approved.")

        total_discrepancy_val = Decimal('0.00')

        for item in reconciliation.items.select_related('product'):
            diff = item.physical_quantity - item.system_quantity
            item.discrepancy_quantity = diff
            item.discrepancy_cost = diff * item.product.unit_cost
            item.save()

            total_discrepancy_val += abs(item.discrepancy_cost)

            if diff != Decimal('0.00'):
                # Execute physical count adjustment
                StockMovementService.record_movement(
                    product=item.product,
                    warehouse=reconciliation.warehouse,
                    movement_type=MovementType.COUNT_ADJUSTMENT,
                    quantity=diff,
                    reference_doc_type='StockReconciliation',
                    reference_doc_id=reconciliation.reconciliation_number,
                    performed_by=supervisor,
                    notes=f"Reconciliation count adjustment approved by supervisor. Diff: {diff} units."
                )

        reconciliation.status = ReconciliationStatus.APPROVED
        reconciliation.reviewed_by = supervisor
        reconciliation.approved_at = timezone.now()
        reconciliation.total_discrepancy_value = total_discrepancy_val
        reconciliation.save()

        # Audit ledger log
        AuditLog.record_event(
            event_type='RECONCILIATION_APPROVED',
            entity_type='STOCK_RECONCILIATION',
            entity_id=str(reconciliation.id),
            actor=supervisor,
            state_after={
                'reconciliation_number': reconciliation.reconciliation_number,
                'total_discrepancy_value': str(total_discrepancy_val),
                'status': ReconciliationStatus.APPROVED
            }
        )

        return reconciliation
