import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from apps.inventory.models import Product


class SupplierStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Active / Approved')
    PROBATION = 'PROBATION', _('Probationary / Under Observation')
    SUSPENDED = 'SUSPENDED', _('Suspended (Disputes / Failures)')
    INACTIVE = 'INACTIVE', _('Inactive')


class PaymentTerms(models.TextChoices):
    IMMEDIATE = 'IMMEDIATE', _('Immediate / Advance Payment')
    NET_15 = 'NET_15', _('Net 15 Days')
    NET_30 = 'NET_30', _('Net 30 Days')
    NET_45 = 'NET_45', _('Net 45 Days')
    NET_60 = 'NET_60', _('Net 60 Days')


class Supplier(TimeStampedModel):
    """
    Supplier Master Directory.
    Maintains verified vendor profiles, performance scores, and contractual terms.
    """
    code = models.CharField(max_length=30, unique=True, db_index=True)
    legal_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=150)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=30)
    address = models.TextField()
    payment_terms = models.CharField(
        max_length=50,
        choices=PaymentTerms.choices,
        default=PaymentTerms.NET_30
    )
    reliability_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text=_('Historical delivery compliance score [0-100].')
    )
    quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text=_('Goods receipt quality & defect-free score [0-100].')
    )
    lead_time_compliance_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    status = models.CharField(
        max_length=20,
        choices=SupplierStatus.choices,
        default=SupplierStatus.ACTIVE,
        db_index=True
    )

    class Meta:
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers Directory')
        ordering = ['legal_name']

    def __str__(self):
        return f"{self.code} — {self.legal_name}"

    @property
    def composite_score(self) -> Decimal:
        """
        Explainable composite score:
        Composite = 0.45 * Reliability + 0.35 * Quality + 0.20 * Lead Time Compliance
        """
        return (
            (Decimal('0.45') * self.reliability_score) +
            (Decimal('0.35') * self.quality_score) +
            (Decimal('0.20') * self.lead_time_compliance_rate)
        )


class SupplierProduct(TimeStampedModel):
    """
    Catalog link connecting verified suppliers to products with contracted pricing.
    """
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='supplied_products')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='product_suppliers')
    supplier_sku = models.CharField(max_length=100, blank=True)
    contracted_unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    lead_time_days = models.PositiveIntegerField(default=7)
    minimum_order_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('1.00')
    )
    is_preferred = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Supplier Product Catalog Link')
        verbose_name_plural = _('Supplier Product Catalog Links')
        unique_together = ('supplier', 'product')

    def __str__(self):
        return f"{self.supplier.code} -> {self.product.sku} (${self.contracted_unit_price})"
