from django.urls import path
from .views import SystemHealthDashboardView, HealthStatusAPIView

app_name = 'system_health'

urlpatterns = [
    path('', SystemHealthDashboardView.as_view(), name='dashboard'),
    path('api/probes/', HealthStatusAPIView.as_view(), name='api-probes'),
]
