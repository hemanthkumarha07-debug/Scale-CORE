from django.urls import path
from .views import (
    AutomationControlCenterView, TriggerPipelineView, AutomationTelemetryAPIView
)

app_name = 'automation'

urlpatterns = [
    path('', AutomationControlCenterView.as_view(), name='control-center'),
    path('trigger/', TriggerPipelineView.as_view(), name='trigger-pipeline'),
    path('api/telemetry/', AutomationTelemetryAPIView.as_view(), name='api-telemetry'),
]
