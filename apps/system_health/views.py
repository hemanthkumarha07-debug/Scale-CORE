from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from .models import SystemHealthRecord
from .services import SystemHealthProbeService
from apps.accounts.permissions import ManagerRequiredMixin


class SystemHealthDashboardView(ManagerRequiredMixin, TemplateView):
    """
    Infrastructure & Subsystem Observability Dashboard.
    Part 21 of the Master Specification.
    """
    template_name = 'system_health/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Run real-time empirical probes
        probes = SystemHealthProbeService.run_all_probes()
        context['probes'] = probes
        context['records'] = SystemHealthRecord.objects.all().order_by('-checked_at')[:30]
        return context


class HealthStatusAPIView(APIView):
    """
    REST API endpoint for automated monitoring probes.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        probes = SystemHealthProbeService.run_all_probes()
        return Response({'status': 'success', 'data': probes})
