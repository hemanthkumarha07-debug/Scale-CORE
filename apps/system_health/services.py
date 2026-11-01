import time
import requests
import logging
from decimal import Decimal
from typing import Dict, List, Any
from django.db import connection
from django.conf import settings
from django.utils import timezone

from .models import SystemHealthRecord, SubsystemName, HealthStatus

logger = logging.getLogger('scale_core.system_health')


class SystemHealthProbeService:
    """
    Empirical Subsystem Health Probing Service.
    Part 21 of the Master Specification.
    Strictly forbids fabricated status indicators.
    """

    @classmethod
    def probe_database(cls) -> Dict[str, Any]:
        """Probes relational database connectivity and measures query latency."""
        t0 = time.perf_counter()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            latency = (time.perf_counter() - t0) * 1000.0
            status = HealthStatus.HEALTHY if latency < 100.0 else HealthStatus.DEGRADED
            msg = f"Database responding ({latency:.1f}ms latency)."
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            status = HealthStatus.CRITICAL
            msg = f"Database probe failed: {str(e)}"

        rec = SystemHealthRecord.objects.create(
            subsystem=SubsystemName.POSTGRESQL,
            status=status,
            response_time_ms=round(latency, 2),
            message=msg,
            metrics={'engine': settings.DATABASES['default']['ENGINE']}
        )
        return {'subsystem': 'Database', 'status': status, 'latency_ms': latency, 'message': msg}

    @classmethod
    def probe_ollama(cls) -> Dict[str, Any]:
        """Probes local Ollama Llama 3.2 daemon availability."""
        url = f"{getattr(settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434')}/api/tags"
        t0 = time.perf_counter()
        try:
            resp = requests.get(url, timeout=2)
            latency = (time.perf_counter() - t0) * 1000.0
            if resp.status_code == 200:
                models = resp.json().get('models', [])
                status = HealthStatus.HEALTHY
                msg = f"Ollama operational. {len(models)} local models detected."
            else:
                status = HealthStatus.DEGRADED
                msg = f"Ollama HTTP {resp.status_code} response."
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            status = HealthStatus.UNKNOWN
            msg = f"Local Ollama service unreachable or restricted ({str(e)[:60]}). Deterministic rule fallback is active."

        SystemHealthRecord.objects.create(
            subsystem=SubsystemName.OLLAMA,
            status=status,
            response_time_ms=round(latency, 2),
            message=msg,
            metrics={'url': url}
        )
        return {'subsystem': 'Ollama Local AI', 'status': status, 'latency_ms': latency, 'message': msg}

    @classmethod
    def probe_forecasting_engine(cls) -> Dict[str, Any]:
        """Probes TensorFlow Deep Learning forecasting engine readiness."""
        t0 = time.perf_counter()
        try:
            import tensorflow as tf
            tf_ver = tf.__version__
            latency = (time.perf_counter() - t0) * 1000.0
            status = HealthStatus.HEALTHY
            msg = f"TensorFlow v{tf_ver} runtime ready for LSTM multi-step inference."
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            status = HealthStatus.CRITICAL
            msg = f"Deep learning engine failure: {str(e)}"

        SystemHealthRecord.objects.create(
            subsystem=SubsystemName.FORECASTING,
            status=status,
            response_time_ms=round(latency, 2),
            message=msg,
            metrics={'tensorflow_available': status == HealthStatus.HEALTHY}
        )
        return {'subsystem': 'Forecasting Engine (TensorFlow)', 'status': status, 'latency_ms': latency, 'message': msg}

    @classmethod
    def run_all_probes(cls) -> List[Dict[str, Any]]:
        return [
            cls.probe_database(),
            cls.probe_forecasting_engine(),
            cls.probe_ollama()
        ]
