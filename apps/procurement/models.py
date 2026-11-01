import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.core.models import TimeStampedModel
from apps.inventory.models import Product, Warehouse
from apps.suppliers.models import Supplier


class POStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Draft (Generated)')
    AWAITING_APPROVAL = 'AWAITING_APPROVAL', _('Awaiting Supervisor Approval')
    APPROVED = 'APPROVED', _('Approved (Ready for Dispatch)')
    DISPATCHED = 'DISPATCHED', _('Dispatched to Supplier')
    ACKNOWLEDGED = 'ACKNOWLEDGED', _('Acknowledged by Supplier')
    PARTIALLY_DELIVERED = 'PARTIALLY_DELIVERED', _('Partially Delivered')
    COMPLETED = 'COMPLETED', _('Completed & Reconciled')
    CANCELLED = 'CANCELLED', _('Cancelled / Rejected')


class POCategory(models.TextChoices):
    CATEGORY_B = 'B', _('Category B: Policy-Controlled Autonomous Dispatch')
    CATEGORY_C = 'C', _('Category C: Human Intervention Required (Supervisor Gateway)')


class ProcurementPolicy(TimeStampedModel):
    """
    Autonomous Procurement Gatekeeper Policy.
    Defines financial, risk, and variance ceilings for autonomous order dispatch.
    """
    policy_name = models.CharField(max_length=100, default='Standard Enterprise Operations Policy')
    auto_dispatch_max_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('5000.00'),
        help_text=_('Maximum purchase order value eligible for autonomous dispatch without supervisor signoff.')
    )
    require_approval_above_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('5000.00')
    )
    max_supplier_price_variance_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        help_text=_('Maximum allowable price variance percentage against contracted price.')
    )
    min_supplier_reliability_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('80.00'),
        help_text=_('Minimum supplier composite reliability score for automated ordering.')
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Procurement Policy')
        verbose_name_plural = _('Procurement Policies')

    def __str__(self):
        return f"{self.policy_name} (Auto-Dispatch <= ${self.auto_dispatch_max_value})"


class PurchaseOrder(TimeStampedModel):
    """
    Purchase Order entity managing the complete procurement lifecycle.
    """
    po_number = models.CharField(max_length=50, unique=True, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='purchase_orders')
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(
        max_length=30,
        choices=POStatus.choices,
        default=POStatus.DRAFT,
        db_index=True
    )
    category = models.CharField(
        max_length=2,
        choices=POCategory.choices,
        default=POCategory.CATEGORY_B,
        db_index=True
    )
    generated_by_system = models.BooleanField(default=True)
    ai_justification = models.TextField(
        blank=True,
        help_text=_('Local LLM explanatory context and risk assessment notes.')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='approved_purchase_orders'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    expected_delivery_date = models.DateField()

    class Meta:
        verbose_name = _('Purchase Order')
        verbose_name_plural = _('Purchase Orders')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.po_number} | {self.supplier.code} | ${self.total_amount} ({self.get_status_display()})"

    def recalculate_total(self):
        total = sum((item.quantity * item.unit_price for item in self.items.all()), Decimal('0.00'))
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class PurchaseOrderItem(models.Model):
    """
    Line item belonging to a Purchase Order.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='po_items')
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    quantity_received = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    class Meta:
        verbose_name = _('Purchase Order Item')
        verbose_name_plural = _('Purchase Order Items')

    @property
    def total_price(self) -> Decimal:
        return self.quantity * self.unit_price

    @property
    def pending_quantity(self) -> Decimal:
        return max(Decimal('0.00'), self.quantity - self.quantity_received)
