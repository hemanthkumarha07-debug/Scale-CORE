"""
SCALE.Core URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from apps.core.views import OverviewDashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', OverviewDashboardView.as_view(), name='overview'),
    
    # Inventory Module
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    # Demand Forecasting Module
    path('forecasting/', include('apps.forecasting.urls', namespace='forecasting')),
    # Procurement Module
    path('procurement/', include('apps.procurement.urls', namespace='procurement')),
    # Local AI Operations Module
    path('intelligence/', include('apps.intelligence.urls', namespace='intelligence')),
    # Automation Control Centre Module
    path('automation/', include('apps.automation.urls', namespace='automation')),
    # System Health Module
    path('system-health/', include('apps.system_health.urls', namespace='system_health')),
]
