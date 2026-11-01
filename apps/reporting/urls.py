from django.urls import path
from .views import ReportingDashboardView, ExportInventoryCSVView, ExportProcurementCSVView

app_name = 'reporting'

urlpatterns = [
    path('', ReportingDashboardView.as_view(), name='dashboard'),
    path('export/inventory/', ExportInventoryCSVView.as_view(), name='export-inventory'),
    path('export/procurement/', ExportProcurementCSVView.as_view(), name='export-procurement'),
]
