import logging
import time
from typing import Dict, Optional

from .port import BasePersistence

try:
    from prometheus_client import Counter, Gauge, Histogram  # type: ignore
    PROM_AVAILABLE = True
except Exception as e:  # pragma: no cover - optional dependency
    logging.warning(f"prometheus_client not available for task metrics: {e}")
    PROM_AVAILABLE = False

# Idempotent registration flag (per-process)
_TASK_METRICS_REGISTERED = False

# In-memory timing cache for durations (task_id -> start_time)
_START_TIMES: Dict[str, float] = {}

# Lazily created metric refs
_TASK_STATUS_COUNTER: Optional[Counter] = None
_TASK_BY_NAME_COUNTER: Optional[Counter] = None
_TASK_RUNNING_GAUGE: Optional[Gauge] = None
_TASK_DURATION_HIST: Optional[Histogram] = None


def _ensure_metrics():
    global _TASK_METRICS_REGISTERED
    global _TASK_STATUS_COUNTER, _TASK_BY_NAME_COUNTER, _TASK_RUNNING_GAUGE, _TASK_DURATION_HIST

    if not PROM_AVAILABLE or _TASK_METRICS_REGISTERED:
        return

    try:
        # Import locally to avoid hard dependency at import time
        from ..core.status import TaskStatus  # type: ignore
    except Exception as e:  # pragma: no cover
        logging.info(f"Task metrics not registered (TaskStatus unavailable): {e}")
        return

    # Define metrics
    _TASK_STATUS_COUNTER = Counter(
        'fastpluggy_task_events_total',
        'Total number of task lifecycle events by status',
        labelnames=['status']
    )
    _TASK_BY_NAME_COUNTER = Counter(
        'fastpluggy_task_executions_total',
        'Total number of task executions by name and final status',
        labelnames=['task_name', 'status']
    )
    _TASK_RUNNING_GAUGE = Gauge(
        'fastpluggy_tasks_running',
        'Number of tasks currently running'
    )
    _TASK_DURATION_HIST = Histogram(
        'fastpluggy_task_duration_seconds',
        'Observed duration of tasks by name and final status',
        labelnames=['task_name', 'status'],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300)
    )

    _TASK_METRICS_REGISTERED = True
    logging.info("Initialized FastPluggy task metrics (subscribers.metrics)")


class MetricsPersistence(BasePersistence):
    """
    Event subscriber implementing BasePersistence interface, used purely to
    update Prometheus task lifecycle metrics. Wired via TaskEventBus.subscribe_class.
    """

    def __init__(self) -> None:
        _ensure_metrics()

    # Lifecycle handlers
    def on_created(self, e) -> None:
        if not PROM_AVAILABLE or _TASK_STATUS_COUNTER is None:
            return
        try:
            from ..core.status import TaskStatus
            _TASK_STATUS_COUNTER.labels(status=TaskStatus.CREATED.value).inc()
            _START_TIMES[e.task_id] = time.time()
        except Exception:
            pass

    def on_running(self, e) -> None:
        if not PROM_AVAILABLE or _TASK_STATUS_COUNTER is None or _TASK_RUNNING_GAUGE is None:
            return
        try:
            from ..core.status import TaskStatus
            _TASK_STATUS_COUNTER.labels(status=TaskStatus.RUNNING.value).inc()
            _TASK_RUNNING_GAUGE.inc()
            _START_TIMES[e.task_id] = time.time()
        except Exception:
            pass

    # Finalization helpers
    def _finalize(self, e, final_status: str) -> None:
        if not PROM_AVAILABLE:
            return
        try:
            name = getattr(e.context, 'task_name', None) or getattr(e.context, 'func_name', 'task')
            if _TASK_STATUS_COUNTER:
                _TASK_STATUS_COUNTER.labels(status=final_status).inc()
            if _TASK_BY_NAME_COUNTER:
                _TASK_BY_NAME_COUNTER.labels(task_name=name, status=final_status).inc()
            start = _START_TIMES.pop(e.task_id, None)
            if start is not None and _TASK_DURATION_HIST:
                dur = max(0.0, time.time() - start)
                _TASK_DURATION_HIST.labels(task_name=name, status=final_status).observe(dur)
        except Exception:
            pass
        finally:
            try:
                if _TASK_RUNNING_GAUGE:
                    _TASK_RUNNING_GAUGE.dec()
            except Exception:
                pass

    # Per-final-status handlers (subscribe_class picks these over on_final)
    def on_success(self, e) -> None:
        try:
            from ..core.status import TaskStatus
            self._finalize(e, TaskStatus.SUCCESS.value)
        except Exception:
            pass

    def on_failed(self, e) -> None:
        try:
            from ..core.status import TaskStatus
            self._finalize(e, TaskStatus.FAILED.value)
        except Exception:
            pass

    def on_cancelled(self, e) -> None:
        try:
            from ..core.status import TaskStatus
            self._finalize(e, TaskStatus.CANCELLED.value)
        except Exception:
            pass

    def on_timeout(self, e) -> None:
        try:
            from ..core.status import TaskStatus
            self._finalize(e, TaskStatus.TIMEOUT.value)
        except Exception:
            pass

    def on_skipped(self, e) -> None:
        try:
            from ..core.status import TaskStatus
            self._finalize(e, TaskStatus.SKIPPED.value)
        except Exception:
            pass

    def on_error(self, e) -> None:
        try:
            from ..core.status import TaskStatus
            self._finalize(e, TaskStatus.ERROR.value)
        except Exception:
            pass

    # Fallback for any other finals (including DEAD)
    def on_final(self, e) -> None:
        try:
            status_str = getattr(e, 'status', None)
            status_val = getattr(status_str, 'value', status_str)
            if isinstance(status_val, str):
                self._finalize(e, status_val)
        except Exception:
            pass
