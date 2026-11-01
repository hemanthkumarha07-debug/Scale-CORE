from django.urls import path
from .views import ForecastingDashboardView, ForecastPredictionAPIView

app_name = 'forecasting'

urlpatterns = [
    path('', ForecastingDashboardView.as_view(), name='dashboard'),
    path('api/predict/', ForecastPredictionAPIView.as_view(), name='api-predict'),
]
