import logging
from typing import Dict, Any
from .models import AuditLog

logger = logging.getLogger('scale_core.audit')


class AuditIntegrityService:
    """
    Verifies the cryptographic integrity of the append-only Audit Ledger.
    Detects any database tampering, modified records, or severed hash links.
    """
    @classmethod
    def verify_ledger_chain(cls) -> Dict[str, Any]:
        records = AuditLog.objects.order_by('timestamp').all()
        total_records = records.count()

        if total_records == 0:
            return {
                'verified_records_count': 0,
                'chain_integrity': 'VALID',
                'tampering_detected': False,
                'message': 'Audit ledger is empty (clean genesis).'
            }

        expected_prev_hash = AuditLog.GENESIS_HASH
        for idx, record in enumerate(records):
            # Verify backward linkage
            if record.previous_hash != expected_prev_hash:
                return {
                    'verified_records_count': idx,
                    'chain_integrity': 'CORRUPTED',
                    'tampering_detected': True,
                    'corrupted_record_id': str(record.id),
                    'corrupted_event': record.event_type,
                    'expected_prev_hash': expected_prev_hash,
                    'actual_prev_hash': record.previous_hash,
                    'message': f"Hash linkage broken at record index {idx} (ID: {record.id})."
                }

            # Recompute and verify current hash
            recomputed = record.compute_hash()
            if record.current_hash != recomputed:
                return {
                    'verified_records_count': idx,
                    'chain_integrity': 'CORRUPTED',
                    'tampering_detected': True,
                    'corrupted_record_id': str(record.id),
                    'corrupted_event': record.event_type,
                    'expected_hash': recomputed,
                    'actual_hash': record.current_hash,
                    'message': f"Data tampering detected at record ID {record.id}. Stored hash does not match content."
                }

            expected_prev_hash = record.current_hash

        head_record = records.last()
        return {
            'verified_records_count': total_records,
            'chain_integrity': 'VALID',
            'tampering_detected': False,
            'genesis_hash': AuditLog.GENESIS_HASH,
            'head_hash': head_record.current_hash if head_record else '',
            'message': f"All {total_records} audit records cryptographically verified."
        }
