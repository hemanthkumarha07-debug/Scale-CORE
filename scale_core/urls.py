"""
SCALE.Core URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from apps.core.views import OverviewDashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', OverviewDashboardView.as_view(), name='overview'),
    
    # Authentication & User Management
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),

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
    # Suppliers Module
    path('suppliers/', include('apps.suppliers.urls', namespace='suppliers')),
    # Logistics Module (Goods Receipt & Shipments)
    path('logistics/', include('apps.logistics.urls', namespace='logistics')),
    # Cryptographic Audit Ledger Module
    path('audit/', include('apps.audit.urls', namespace='audit')),
    # Financial Intelligence Module
    path('finance/', include('apps.finance.urls', namespace='finance')),
    # Notifications Module
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    # System Health Module
    path('system-health/', include('apps.system_health.urls', namespace='system_health')),
    # Reporting Module
    path('reporting/', include('apps.reporting.urls', namespace='reporting')),
]
