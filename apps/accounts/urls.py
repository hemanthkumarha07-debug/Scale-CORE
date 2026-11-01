from django.urls import path
from .views import SCALELoginView, SCALELogoutView

app_name = 'accounts'

urlpatterns = [
    path('login/', SCALELoginView.as_view(), name='login'),
    path('logout/', SCALELogoutView.as_view(), name='logout'),
]
