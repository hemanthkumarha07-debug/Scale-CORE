import hashlib
import json
import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class AuditLog(models.Model):
    """
    Append-Only Cryptographic Audit Ledger.
    Every state change in SCALE.Core is hashed, chained to the previous record,
    and permanently recorded. Modifying or deleting rows is strictly forbidden.
    """
    GENESIS_HASH = "0" * 64

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='audit_records'
    )
    actor_username = models.CharField(max_length=150, default='SYSTEM')
    actor_role = models.CharField(max_length=20, default='SYSTEM')
    event_type = models.CharField(max_length=100, db_index=True)
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=100, db_index=True)
    state_before = models.JSONField(default=dict, blank=True)
    state_after = models.JSONField(default=dict, blank=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, editable=False)
    previous_hash = models.CharField(max_length=64, db_index=True, editable=False)
    current_hash = models.CharField(max_length=64, unique=True, db_index=True, editable=False)

    class Meta:
        verbose_name = _('Audit Log Record')
        verbose_name_plural = _('Audit Log Ledger')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['previous_hash', 'current_hash']),
        ]

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.event_type} on {self.entity_type}#{self.entity_id} by {self.actor_username}"

    def clean(self):
        if not self._state.adding:
            raise ValidationError(_('AuditLog entries are immutable and cannot be updated.'))

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(_('AuditLog is strictly append-only. UPDATE operations are forbidden.'))
        
        # Determine previous hash in chain
        if not self.previous_hash:
            last_record = AuditLog.objects.order_by('-timestamp').first()
            self.previous_hash = last_record.current_hash if last_record else self.GENESIS_HASH

        # Compute current cryptographic hash
        self.current_hash = self.compute_hash()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_('AuditLog is strictly append-only. DELETE operations are forbidden.'))

    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash chaining the previous record, actor, event,
        timestamp, and state changes.
        """
        payload = {
            'previous_hash': self.previous_hash,
            'actor_username': self.actor_username,
            'actor_role': self.actor_role,
            'event_type': self.event_type,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id),
            'state_before': self.state_before,
            'state_after': self.state_after,
            'timestamp': self.timestamp.isoformat() if self.timestamp else ''
        }
        raw_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        return hashlib.sha256(raw_bytes).hexdigest()

    @classmethod
    def record_event(
        cls,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor=None,
        state_before: dict = None,
        state_after: dict = None,
        source_ip: str = None,
        request_id: str = ''
    ) -> 'AuditLog':
        """
        Factory helper to record an auditable event with cryptographic chaining.
        """
        username = 'SYSTEM'
        role = 'SYSTEM'
        if actor and getattr(actor, 'is_authenticated', False):
            username = actor.username
            role = getattr(actor, 'role', 'EMPLOYEE')

        return cls.objects.create(
            actor=actor if (actor and getattr(actor, 'is_authenticated', False)) else None,
            actor_username=username,
            actor_role=role,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=str(entity_id),
            state_before=state_before or {},
            state_after=state_after or {},
            source_ip=source_ip,
            request_id=request_id
        )
