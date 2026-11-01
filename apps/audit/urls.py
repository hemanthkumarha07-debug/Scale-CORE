from django.urls import path
from .views import AuditLedgerView

app_name = 'audit'

urlpatterns = [
    path('', AuditLedgerView.as_view(), name='ledger'),
]
