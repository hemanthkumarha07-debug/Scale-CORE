from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from .services import OperationalAIAdvisor
from apps.accounts.permissions import ManagerRequiredMixin


class AIOperationsWorkspaceView(ManagerRequiredMixin, TemplateView):
    """
    Local AI Operations Copilot Workspace.
    Part 18 of the Master Specification.
    """
    template_name = 'intelligence/workspace.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Sample quick questions
        context['quick_prompts'] = [
            "Which products are currently at critical stockout risk?",
            "What purchase orders are pending supervisor approval and why?",
            "What is our current excess inventory and capital at risk?",
            "Explain why SKU-ELEC-4091 has an order draft of 450 units.",
        ]
        return context


class AIQueryAPIView(APIView):
    """
    REST API endpoint for context-aware operational questions.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'status': 'error', 'message': 'Query cannot be empty.'}, status=400)

        result = OperationalAIAdvisor.answer_operational_query(query, user=request.user)
        return Response({'status': 'success', 'data': result})
