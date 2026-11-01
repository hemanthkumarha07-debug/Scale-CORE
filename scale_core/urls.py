"""
SCALE.Core URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from apps.core.views import OverviewDashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', OverviewDashboardView.as_view(), name='overview'),
    
    # Core Modular API Routes
    # path('api/v1/auth/', include('apps.accounts.urls')),
    # path('api/v1/inventory/', include('apps.inventory.urls')),
]
