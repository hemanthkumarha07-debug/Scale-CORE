from django.views.generic import TemplateView, View
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from .models import AutomationWorkflow, WorkflowExecution, WorkflowStatus
from .services import AutonomousWorkflowOrchestrator
from apps.accounts.permissions import ManagerRequiredMixin


class AutomationControlCenterView(ManagerRequiredMixin, TemplateView):
    """
    Centralized Automation Command Center.
    Part 16 of the Master Specification.
    """
    template_name = 'automation/control_center.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        telemetry = AutonomousWorkflowOrchestrator.get_automation_telemetry()
        context['telemetry'] = telemetry
        context['executions'] = WorkflowExecution.objects.select_related('workflow').order_by('-initiated_at')[:25]
        context['workflows'] = AutomationWorkflow.objects.all().order_by('name')
        return context


class TriggerPipelineView(ManagerRequiredMixin, View):
    """
    Executes the autonomous 02:00 AM operational cycle on demand.
    """
    def post(self, request):
        execution = AutonomousWorkflowOrchestrator.execute_nightly_autonomous_pipeline(actor=request.user)
        messages.success(
            request,
            f"Autonomous operational cycle completed! Execution status: {execution.status}. "
            f"Stages completed: {len(execution.execution_context.get('stages_completed', []))}."
        )
        return redirect('automation:control-center')


class AutomationTelemetryAPIView(APIView):
    """
    REST API endpoint for real-time automation metrics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        telemetry = AutonomousWorkflowOrchestrator.get_automation_telemetry()
        return Response({'status': 'success', 'data': telemetry})
