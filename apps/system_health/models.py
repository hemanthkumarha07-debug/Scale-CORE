import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class SubsystemName(models.TextChoices):
    POSTGRESQL = 'POSTGRESQL', _('PostgreSQL Relational Database')
    REDIS = 'REDIS', _('Redis Message Broker & Cache')
    CELERY_WORKER = 'CELERY_WORKER', _('Celery Background Task Workers')
    CELERY_BEAT = 'CELERY_BEAT', _('Celery Beat Periodic Scheduler')
    OLLAMA = 'OLLAMA', _('Ollama Local Generative AI Service')
    FORECASTING = 'FORECASTING', _('TensorFlow Deep Learning Forecasting Engine')
    APPLICATION = 'APPLICATION', _('Django Core Application & Memory')


class HealthStatus(models.TextChoices):
    HEALTHY = 'HEALTHY', _('Healthy / Operational')
    DEGRADED = 'DEGRADED', _('Degraded Performance')
    CRITICAL = 'CRITICAL', _('Critical Failure / Unreachable')
    UNKNOWN = 'UNKNOWN', _('Unknown / Unmonitored')


class SystemHealthRecord(models.Model):
    """
    Empirical telemetry snapshot for an individual system component.
    Strictly forbids fabricated healthy indicators.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subsystem = models.CharField(max_length=50, choices=SubsystemName.choices, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=HealthStatus.choices,
        default=HealthStatus.UNKNOWN,
        db_index=True
    )
    response_time_ms = models.FloatField(default=0.0)
    message = models.TextField(blank=True)
    metrics = models.JSONField(default=dict, blank=True)
    checked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _('System Health Record')
        verbose_name_plural = _('System Health Telemetry')
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['subsystem', 'checked_at']),
        ]

    def __str__(self):
        return f"{self.subsystem}: {self.status} ({self.response_time_ms:.1f}ms) @ {self.checked_at}"
