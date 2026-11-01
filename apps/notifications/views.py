from django.views.generic import ListView, View
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from .models import Notification
from apps.accounts.permissions import OperationalRequiredMixin


class NotificationHubView(OperationalRequiredMixin, ListView):
    """
    Centralized Alert & Operational Exception Hub.
    Part 19 of the Master Specification.
    """
    model = Notification
    template_name = 'notifications/hub.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        return Notification.objects.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(is_read=False).count()
        context['critical_count'] = Notification.objects.filter(priority='CRITICAL', is_acknowledged=False).count()
        return context


class AcknowledgeNotificationView(OperationalRequiredMixin, View):
    """Marks an alert acknowledged by the operator."""
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk)
        notif.is_read = True
        notif.is_acknowledged = True
        notif.acknowledged_by = request.user
        notif.acknowledged_at = timezone.now()
        notif.save(update_fields=['is_read', 'is_acknowledged', 'acknowledged_by', 'acknowledged_at'])
        return redirect('notifications:hub')
