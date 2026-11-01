import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class NotificationCategory(models.TextChoices):
    CRITICAL_INVENTORY = 'CRITICAL_INVENTORY', _('Critical Inventory / Stockout Risk')
    PROCUREMENT = 'PROCUREMENT', _('Procurement & Approvals')
    SUPPLIER_DELAYS = 'SUPPLIER_DELAYS', _('Supplier Delays & Performance')
    LOGISTICS = 'LOGISTICS', _('Logistics & Shipment Discrepancies')
    FINANCIAL_EXCEPTIONS = 'FINANCIAL_EXCEPTIONS', _('Financial & Capital at Risk')
    AI_RECOMMENDATION = 'AI_RECOMMENDATION', _('AI Operations Recommendation')
    AUTOMATION_FAILURE = 'AUTOMATION_FAILURE', _('Autonomous Workflow Exception')
    SECURITY_EVENT = 'SECURITY_EVENT', _('Security & Privilege Event')
    SYSTEM_HEALTH = 'SYSTEM_HEALTH', _('Infrastructure & System Health')


class NotificationPriority(models.TextChoices):
    CRITICAL = 'CRITICAL', _('Critical (Immediate Attention)')
    WARNING = 'WARNING', _('Warning (Action Required)')
    INFO = 'INFO', _('Information')


class Notification(models.Model):
    """
    Centralized notification and exception management entity.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text=_('Target user, or null for broadcast to all managers.')
    )
    category = models.CharField(
        max_length=40,
        choices=NotificationCategory.choices,
        default=NotificationCategory.SYSTEM_HEALTH,
        db_index=True
    )
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.INFO,
        db_index=True
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    action_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_notifications'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.priority}] {self.title}"
