import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.core.models import TimeStampedModel
from apps.procurement.models import PurchaseOrder
from apps.inventory.models import Product


class ShipmentStatus(models.TextChoices):
    CREATED = 'CREATED', _('Created / Awaiting Carrier')
    DISPATCHED = 'DISPATCHED', _('Dispatched from Vendor')
    IN_TRANSIT = 'IN_TRANSIT', _('In Transit')
    DELAYED = 'DELAYED', _('Delivery Delayed')
    OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', _('Out for Delivery to Warehouse')
    DELIVERED = 'DELIVERED', _('Delivered to Warehouse Dock')
    EXCEPTION = 'EXCEPTION', _('Logistics Exception / Dispute')
    CANCELLED = 'CANCELLED', _('Cancelled')


class Shipment(TimeStampedModel):
    """
    Logistics shipment tracking entity linked to a Purchase Order.
    """
    tracking_number = models.CharField(max_length=100, unique=True, db_index=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='shipments')
    carrier_name = models.CharField(max_length=100)
    dispatch_date = models.DateField()
    expected_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    freight_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(
        max_length=30,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.CREATED,
        db_index=True
    )
    is_delayed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Shipment')
        verbose_name_plural = _('Shipments')
        ordering = ['-dispatch_date']

    def __str__(self):
        return f"{self.tracking_number} ({self.carrier_name}) - {self.get_status_display()}"


class GoodsReceipt(TimeStampedModel):
    """
    Formal dock receiving document.
    Documents the physical arrival and verification of inbound goods.
    """
    receipt_number = models.CharField(max_length=50, unique=True, db_index=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='goods_receipts')
    shipment = models.ForeignKey(Shipment, on_delete=models.SET_NULL, null=True, blank=True, related_name='receipts')
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='received_shipments'
    )
    discrepancy_detected = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Goods Receipt')
        verbose_name_plural = _('Goods Receipts')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.receipt_number} for {self.purchase_order.po_number}"


class GoodsReceiptItem(models.Model):
    """
    Line item verified during goods receipt inspection.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='receipt_items')
    quantity_expected = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_damaged = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Goods Receipt Item')
        verbose_name_plural = _('Goods Receipt Items')

    @property
    def has_discrepancy(self) -> bool:
        return (self.quantity_expected != self.quantity_received) or (self.quantity_damaged > 0)
