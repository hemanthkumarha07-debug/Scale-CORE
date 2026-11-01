import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from apps.inventory.models import Product, Warehouse


class DailySalesLog(models.Model):
    """
    Historical sales and demand record.
    Forms the foundational data pipeline for LSTM demand forecasting,
    feature engineering, and stockout censoring detection.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(db_index=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='daily_sales')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='daily_sales')
    units_sold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    sales_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00')
    )
    was_stockout_day = models.BooleanField(
        default=False,
        help_text=_('True if on-hand stock reached zero on this day. Prevents treating stockouts as zero true demand.')
    )
    is_promotion_active = models.BooleanField(
        default=False,
        help_text=_('True if marketing promotions or pricing discounts were active.')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Daily Sales Log')
        verbose_name_plural = _('Daily Sales Logs')
        unique_together = ('date', 'product', 'warehouse')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['product', 'date']),
            models.Index(fields=['warehouse', 'date']),
        ]

    def __str__(self):
        return f"{self.date} | {self.product.sku}: {self.units_sold} units (${self.sales_revenue})"
