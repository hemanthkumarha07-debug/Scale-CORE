from django.urls import path
from .views import SupplierListView

app_name = 'suppliers'

urlpatterns = [
    path('', SupplierListView.as_view(), name='list'),
]
