from decimal import Decimal
from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, F, Sum
from rest_framework import viewsets, permissions
from rest_framework.serializers import ModelSerializer

from .models import Product, Warehouse, InventoryBalance, InventoryMovement, StockReconciliation, MovementType
from .services import StockMovementService, InventoryClassificationService, StockReconciliationService
from apps.accounts.permissions import ManagerRequiredMixin, OperationalRequiredMixin, IsManagerUser, IsOperationalUser


# ---------------------------------------------------------
# Web Views (Enterprise Hybrid UI)
# ---------------------------------------------------------

class InventoryCatalogView(OperationalRequiredMixin, ListView):
    """
    Product Master and Inventory Balances Telemetry.
    """
    model = InventoryBalance
    template_name = 'inventory/catalog.html'
    context_object_name = 'balances'
    paginate_by = 25

    def get_queryset(self):
        qs = InventoryBalance.objects.select_related('product', 'product__category', 'warehouse').order_by('product__sku')
        search_query = self.request.GET.get('q')
        category = self.request.GET.get('category')
        abc = self.request.GET.get('abc')

        if search_query:
            qs = qs.filter(Q(product__sku__icontains=search_query) | Q(product__name__icontains=search_query))
        if category:
            qs = qs.filter(product__category__code=category)
        if abc:
            qs = qs.filter(product__abc_class=abc)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_items'] = Product.objects.count()
        context['total_valuation'] = InventoryBalance.objects.aggregate(
            val=Sum(F('on_hand_stock') * F('product__unit_cost'))
        )['val'] or Decimal('0.00')
        context['below_rop_count'] = InventoryBalance.objects.filter(on_hand_stock__lt=F('product__reorder_point')).count()
        return context


class InventoryMovementLedgerView(OperationalRequiredMixin, ListView):
    """
    Immutable ledger of all inventory transactions.
    """
    model = InventoryMovement
    template_name = 'inventory/movements.html'
    context_object_name = 'movements'
    paginate_by = 30

    def get_queryset(self):
        return InventoryMovement.objects.select_related('product', 'warehouse', 'performed_by').order_by('-timestamp')


# ---------------------------------------------------------
# Django REST Framework Serializers & ViewSets
# ---------------------------------------------------------

class ProductSerializer(ModelSerializer):
    category_name = ModelSerializer.serializer_related_field = 'category.name'

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'category', 'unit_of_measure',
            'unit_cost', 'unit_price', 'abc_class', 'xyz_class',
            'reorder_point', 'safety_stock', 'minimum_order_qty',
            'lead_time_days_avg', 'status'
        ]


class InventoryBalanceSerializer(ModelSerializer):
    sku = ModelSerializer.serializer_related_field = 'product.sku'
    product_name = ModelSerializer.serializer_related_field = 'product.name'
    warehouse_code = ModelSerializer.serializer_related_field = 'warehouse.code'

    class Meta:
        model = InventoryBalance
        fields = [
            'id', 'product', 'warehouse', 'sku', 'product_name', 'warehouse_code',
            'on_hand_stock', 'reserved_stock', 'incoming_stock', 'damaged_stock',
            'available_stock', 'projected_stock', 'is_below_rop'
        ]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]


class InventoryBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryBalance.objects.select_related('product', 'warehouse').all()
    serializer_class = InventoryBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
