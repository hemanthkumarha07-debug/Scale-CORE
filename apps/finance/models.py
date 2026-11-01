import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.inventory.models import Product, Warehouse


class FinancialSnapshot(models.Model):
    """
    Daily financial balance and exposure snapshot.
    Provides management telemetry on inventory working capital and commitments.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot_date = models.DateField(unique=True, db_index=True)
    total_inventory_valuation = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))
    total_capital_at_risk = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Valuation of excess stock exceeding max safety ceilings.')
    )
    total_excess_inventory_value = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))
    annual_holding_cost_projected = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_pending_po_commitments = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Financial Snapshot')
        verbose_name_plural = _('Financial Snapshots')
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"{self.snapshot_date}: Valuation=${self.total_inventory_valuation} | Risk=${self.total_capital_at_risk}"


class ExcessInventoryRecord(models.Model):
    """
    Itemized excess stock valuation report per SKU.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot = models.ForeignKey(FinancialSnapshot, on_delete=models.CASCADE, related_name='excess_items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='excess_records')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    on_hand_stock = models.DecimalField(max_digits=12, decimal_places=2)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2)
    excess_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    excess_valuation = models.DecimalField(max_digits=14, decimal_places=2)
    holding_cost_annual = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = _('Excess Inventory Record')
        verbose_name_plural = _('Excess Inventory Records')
