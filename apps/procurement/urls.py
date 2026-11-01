from django.urls import path
from .views import (
    PurchaseOrderListView, PurchaseOrderDetailView,
    ApprovePurchaseOrderView, RejectPurchaseOrderView
)

app_name = 'procurement'

urlpatterns = [
    path('', PurchaseOrderListView.as_view(), name='orders-list'),
    path('orders/', PurchaseOrderListView.as_view(), name='orders-list-alias'),
    path('orders/<uuid:pk>/', PurchaseOrderDetailView.as_view(), name='order-detail'),
    path('orders/<uuid:pk>/approve/', ApprovePurchaseOrderView.as_view(), name='order-approve'),
    path('orders/<uuid:pk>/reject/', RejectPurchaseOrderView.as_view(), name='order-reject'),
]
