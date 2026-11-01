from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InventoryCatalogView, InventoryMovementLedgerView,
    ProductViewSet, InventoryBalanceViewSet
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='api-products')
router.register(r'balances', InventoryBalanceViewSet, basename='api-balances')

app_name = 'inventory'

urlpatterns = [
    path('', InventoryCatalogView.as_view(), name='catalog'),
    path('movements/', InventoryMovementLedgerView.as_view(), name='movements'),
    path('api/', include(router.urls)),
]
