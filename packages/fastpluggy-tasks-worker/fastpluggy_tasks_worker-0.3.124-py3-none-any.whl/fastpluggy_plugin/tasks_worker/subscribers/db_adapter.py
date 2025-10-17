# tasks/persistence/db_adapter.py
import logging
from datetime import datetime, UTC

from .port import BasePersistence
from ..core.events import TaskLifecycleEvent
from ..core.status import TaskStatus
from ..persistence.repository.context import save_context
from ..persistence.repository.report import (
    init_report_from_context,
    save_report,
    update_report,
)

log = logging.getLogger("DBPersistence")


class DBPersistence(BasePersistence):
    """
    Idempotent(ish) persistence adapter.
    - RUNNING: ensure context saved, create initial report row
    - FINAL (SUCCESS/FAILED/CANCELLED/SKIPPED/DEAD/TIMEOUT): update report
    - SKIPPED: write a minimal skipped report if none exists
    """

    def on_created(self, e: TaskLifecycleEvent) -> None:
        """Persist context as soon as a task is created/submitted."""
        try:
            save_context(e.context)
        except Exception:
            log.exception("persist created failed (non-fatal)")

    def on_running(self, e: TaskLifecycleEvent) -> None:
        ctx = e.context
        try:
            # In case QUEUED wasn't persisted at submit time
            save_context(ctx)
        except Exception:
            log.exception("save_context failed (non-fatal)")

        try:
            report = init_report_from_context(ctx)
            report.worker_id = getattr(ctx, "worker_id", None)
            # If you want a "started_at" timestamp on report, set it here.
            save_report(report)  # should be safe if you do get-or-create in repo
        except Exception:
            log.exception("save_report (init) failed (non-fatal)")

    def on_final(self, e: TaskLifecycleEvent) -> None:
        ctx = e.context
        try:
            # Build a report snapshot and push update
            report = init_report_from_context(ctx)
            report.end_time = datetime.now(UTC)
            report.status = e.status
            # pull logs from the runner-attached handler if present
            log_handler = getattr(ctx, "thread_handler", None)
            if log_handler:
                try:
                    report.logs = log_handler.get_stream_value()
                except Exception:
                    pass
            update_report(report)
        except Exception:
            log.exception("update_report failed (non-fatal)")

    def on_skipped(self, e: TaskLifecycleEvent) -> None:
        ctx = e.context
        try:
            report = init_report_from_context(ctx)
            report.status = TaskStatus.SKIPPED
            report.end_time = datetime.now(UTC)
            report.logs = (report.logs or "") + "⛔ Task skipped due to concurrency lock."
            update_report(report)
        except Exception:
            log.exception("persist skipped failed (non-fatal)")
