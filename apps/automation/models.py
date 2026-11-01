import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class WorkflowStatus(models.TextChoices):
    QUEUED = 'QUEUED', _('Queued')
    RUNNING = 'RUNNING', _('Running')
    COMPLETED = 'COMPLETED', _('Completed')
    FAILED = 'FAILED', _('Failed')
    RETRYING = 'RETRYING', _('Retrying')
    SUSPENDED = 'SUSPENDED', _('Suspended')
    AWAITING_APPROVAL = 'AWAITING_APPROVAL', _('Awaiting Human Approval')
    CANCELLED = 'CANCELLED', _('Cancelled')
    RECONCILIATION_REQUIRED = 'RECONCILIATION_REQUIRED', _('Reconciliation Required')


class ExecutionCategory(models.TextChoices):
    CATEGORY_A = 'A', _('Category A: Fully Autonomous')
    CATEGORY_B = 'B', _('Category B: Policy-Controlled Autonomous')
    CATEGORY_C = 'C', _('Category C: Human Intervention Required')


class AutomationWorkflow(TimeStampedModel):
    """
    Registry of autonomous workflow definitions in SCALE.Core.
    """
    name = models.CharField(max_length=100, unique=True)
    workflow_type = models.CharField(max_length=50, db_index=True)
    description = models.TextField(blank=True)
    execution_category = models.CharField(
        max_length=2,
        choices=ExecutionCategory.choices,
        default=ExecutionCategory.CATEGORY_A
    )
    is_enabled = models.BooleanField(default=True)
    max_retries = models.PositiveSmallIntegerField(default=3)
    timeout_seconds = models.PositiveIntegerField(default=300)

    class Meta:
        verbose_name = _('Automation Workflow')
        verbose_name_plural = _('Automation Workflows')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} [{self.execution_category}]"


class WorkflowExecution(models.Model):
    """
    Transactional record of an individual workflow execution instance.
    Guarantees idempotency and state transition integrity.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(AutomationWorkflow, on_delete=models.PROTECT, related_name='executions')
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    status = models.CharField(
        max_length=30,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.QUEUED,
        db_index=True
    )
    related_entity_type = models.CharField(max_length=100, blank=True)
    related_entity_id = models.CharField(max_length=100, blank=True)
    initiated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    error_message = models.TextField(blank=True)
    execution_context = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _('Workflow Execution')
        verbose_name_plural = _('Workflow Executions')
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['workflow', 'status']),
            models.Index(fields=['status', 'initiated_at']),
        ]

    def __str__(self):
        return f"{self.workflow.name} [{self.status}] (Key: {self.idempotency_key[:12]}...)"

    @property
    def duration_seconds(self) -> float:
        if self.completed_at and self.initiated_at:
            return (self.completed_at - self.initiated_at).total_seconds()
        return 0.0

    def mark_completed(self, context_update: dict = None):
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = timezone.now()
        if context_update:
            self.execution_context.update(context_update)
        self.save(update_fields=['status', 'completed_at', 'execution_context'])

    def mark_failed(self, error_msg: str):
        self.status = WorkflowStatus.FAILED
        self.completed_at = timezone.now()
        self.error_message = error_msg
        self.save(update_fields=['status', 'completed_at', 'error_message'])
