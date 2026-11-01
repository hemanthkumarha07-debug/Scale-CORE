import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class SCALEUserRole(models.TextChoices):
    MANAGER = 'MANAGER', _('Manager / System Supervisor')
    EMPLOYEE = 'EMPLOYEE', _('Employee / Operational User')


class SCALEUser(AbstractUser):
    """
    Custom user model for SCALE.Core platform.
    Strictly enforces the two-tier organizational authority model:
    - MANAGER: Full operational supervisor authority (finance, AI copilot, policy controls, approvals).
    - EMPLOYEE: Restricted operational tasks only (physical count input, goods receipt verification).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20,
        choices=SCALEUserRole.choices,
        default=SCALEUserRole.EMPLOYEE,
        help_text=_('System authorization tier. Determines module accessibility and decision authority.')
    )
    department = models.CharField(max_length=100, default='Supply Chain Operations')
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('SCALE User')
        verbose_name_plural = _('SCALE Users')
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_manager(self) -> bool:
        """Returns True if the user is a designated Manager/Supervisor or superuser."""
        return self.role == SCALEUserRole.MANAGER or self.is_superuser

    @property
    def is_employee(self) -> bool:
        """Returns True if user is an operational employee."""
        return self.role == SCALEUserRole.EMPLOYEE and not self.is_superuser

    def can_access_financials(self) -> bool:
        """Manager only: access to financial margins, holding costs, and capital-at-risk."""
        return self.is_manager

    def can_approve_procurement(self) -> bool:
        """Manager only: authorization to approve Category C high-risk purchase orders."""
        return self.is_manager

    def can_configure_automation(self) -> bool:
        """Manager only: authorization to modify autonomous policies and thresholds."""
        return self.is_manager

    def can_inspect_audit_ledger(self) -> bool:
        """Manager only: permission to view cryptographic audit records."""
        return self.is_manager
