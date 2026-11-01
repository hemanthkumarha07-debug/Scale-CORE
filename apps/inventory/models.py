import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.core.models import TimeStampedModel


class ABCClass(models.TextChoices):
    A = 'A', _('Class A (High Value / Critical)')
    B = 'B', _('Class B (Moderate Value)')
    C = 'C', _('Class C (Low Value / Bulk)')


class XYZClass(models.TextChoices):
    X = 'X', _('Class X (Constant Demand / Low Volatility)')
    Y = 'Y', _('Class Y (Fluctuating Demand / Moderate Volatility)')
    Z = 'Z', _('Class Z (Irregular Demand / High Volatility)')


class ProductStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Active')
    DISCONTINUED = 'DISCONTINUED', _('Discontinued')
    UNDER_REVIEW = 'UNDER_REVIEW', _('Under Review')


class MovementType(models.TextChoices):
    GOODS_RECEIPT = 'GOODS_RECEIPT', _('Goods Receipt (Inbound)')
    SALES_DISPATCH = 'SALES_DISPATCH', _('Sales Dispatch (Outbound)')
    INTERNAL_TRANSFER = 'INTERNAL_TRANSFER', _('Internal Warehouse Transfer')
    DAMAGE_WRITEOFF = 'DAMAGE_WRITEOFF', _('Damaged Goods Write-off')
    COUNT_ADJUSTMENT = 'COUNT_ADJUSTMENT', _('Physical Count Adjustment')
    RETURN = 'RETURN', _('Customer / Supplier Return')


class Warehouse(TimeStampedModel):
    """
    Physical storage and fulfillment facility.
    """
    code = models.CharField(max_length=30, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    total_capacity_sqft = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Warehouse')
        verbose_name_plural = _('Warehouses')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"


class ProductCategory(TimeStampedModel):
    """
    Taxonomy and classification group for inventory items.
    """
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    holding_cost_rate_annual = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.2000'),
        help_text=_('Annual inventory carrying cost percentage (e.g. 0.20 = 20%).')
    )

    class Meta:
        verbose_name = _('Product Category')
        verbose_name_plural = _('Product Categories')
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    """
    Product Master record. Central entity for all inventory, forecasting,
    and autonomous procurement operations.
    """
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    unit_of_measure = models.CharField(max_length=20, default='UNIT')
    description = models.TextField(blank=True)
    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    abc_class = models.CharField(max_length=1, choices=ABCClass.choices, blank=True, null=True, db_index=True)
    xyz_class = models.CharField(max_length=1, choices=XYZClass.choices, blank=True, null=True, db_index=True)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    safety_stock = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    minimum_order_qty = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1.00'))
    order_multiple = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1.00'))
    lead_time_days_avg = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('7.00'))
    lead_time_days_std = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('1.50'))
    service_level_target = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=Decimal('0.950'),
        validators=[MinValueValidator(Decimal('0.500')), MaxValueValidator(Decimal('0.999'))]
    )
    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE,
        db_index=True
    )

    class Meta:
        verbose_name = _('Product Master')
        verbose_name_plural = _('Product Catalog')
        ordering = ['sku']

    def __str__(self):
        return f"{self.sku} — {self.name}"


class InventoryBalance(models.Model):
    """
    Current stock position for a product in a specific warehouse.
    Maintains strict physical and available inventory accounting.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='balances')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='balances')
    on_hand_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    reserved_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    incoming_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    damaged_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    storage_bin = models.CharField(max_length=50, blank=True)
    last_recounted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Inventory Balance')
        verbose_name_plural = _('Inventory Balances')
        unique_together = ('product', 'warehouse')
        indexes = [
            models.Index(fields=['product', 'warehouse']),
        ]

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.code}: On-Hand={self.on_hand_stock}"

    @property
    def available_stock(self) -> Decimal:
        """Available Stock = Physical On-Hand - Reserved"""
        return max(Decimal('0.00'), self.on_hand_stock - self.reserved_stock)

    @property
    def projected_stock(self) -> Decimal:
        """Projected Position = Available Stock + Confirmed Incoming Orders"""
        return self.available_stock + self.incoming_stock

    @property
    def total_valuation(self) -> Decimal:
        """Current financial valuation of on-hand inventory."""
        return self.on_hand_stock * self.product.unit_cost

    @property
    def is_below_rop(self) -> bool:
        """True if projected inventory is strictly below the reorder point."""
        return self.projected_stock < self.product.reorder_point


class InventoryMovement(models.Model):
    """
    Immutable ledger of all physical inventory stock changes.
    Every movement creates a permanent transactional record.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_number = models.CharField(max_length=50, unique=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='movements')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField(max_length=30, choices=MovementType.choices, db_index=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reference_doc_type = models.CharField(max_length=50, blank=True)
    reference_doc_id = models.CharField(max_length=100, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _('Inventory Movement')
        verbose_name_plural = _('Inventory Movements')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.transaction_number}: {self.movement_type} {self.quantity} of {self.product.sku}"


class ReconciliationStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Draft Count')
    SUBMITTED = 'SUBMITTED', _('Submitted by Operator')
    UNDER_REVIEW = 'UNDER_REVIEW', _('Under Supervisor Review')
    APPROVED = 'APPROVED', _('Approved & Adjusted')
    REJECTED = 'REJECTED', _('Rejected')


class StockReconciliation(TimeStampedModel):
    """
    Stock reconciliation workflow batch.
    Never automatically overwrites inventory without Supervisor approval.
    """
    reconciliation_number = models.CharField(max_length=50, unique=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='reconciliations')
    status = models.CharField(
        max_length=25,
        choices=ReconciliationStatus.choices,
        default=ReconciliationStatus.DRAFT,
        db_index=True
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_reconciliations'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='reviewed_reconciliations'
    )
    total_discrepancy_value = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Stock Reconciliation')
        verbose_name_plural = _('Stock Reconciliations')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reconciliation_number} ({self.status}) @ {self.warehouse.code}"


class StockReconciliationItem(models.Model):
    """
    Individual item count verification record within a reconciliation batch.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reconciliation = models.ForeignKey(StockReconciliation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='reconciliation_items')
    system_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    physical_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    discrepancy_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    discrepancy_cost = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Reconciliation Item')
        verbose_name_plural = _('Reconciliation Items')

    def save(self, *args, **kwargs):
        self.discrepancy_quantity = self.physical_quantity - self.system_quantity
        self.discrepancy_cost = self.discrepancy_quantity * self.product.unit_cost
        super().save(*args, **kwargs)
