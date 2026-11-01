from django.urls import path
from .views import FinancialIntelligenceView

app_name = 'finance'

urlpatterns = [
    path('', FinancialIntelligenceView.as_view(), name='dashboard'),
]
