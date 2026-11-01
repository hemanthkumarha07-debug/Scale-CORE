from django.views import View
from django.shortcuts import render
from apps.accounts.permissions import ManagerRequiredMixin
from .models import AuditLog
from .services import AuditIntegrityService

class AuditLedgerView(ManagerRequiredMixin, View):
    """
    Append-Only Cryptographic Audit Ledger Console.
    Displays SHA-256 hash chains, tamper detection telemetry, and historical system mutations.
    """
    template_name = 'audit/ledger.html'

    def get(self, request):
        integrity = AuditIntegrityService.verify_ledger_chain()
        records = AuditLog.objects.order_by('-timestamp')[:50]

        return render(request, self.template_name, {
            'integrity': integrity,
            'records': records,
        })
