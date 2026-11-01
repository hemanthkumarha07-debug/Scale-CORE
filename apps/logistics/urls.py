from django.urls import path
from .views import LogisticsDashboardView

app_name = 'logistics'

urlpatterns = [
    path('', LogisticsDashboardView.as_view(), name='dashboard'),
]
