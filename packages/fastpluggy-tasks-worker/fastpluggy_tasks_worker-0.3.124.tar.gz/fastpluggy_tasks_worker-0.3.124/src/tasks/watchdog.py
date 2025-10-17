from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from .. import TaskWorker
from ..config import TasksRunnerSettings
from fastpluggy.core.database import session_scope
from ..core.status import TaskStatus
from ..persistence.models.report import TaskReportDB
from fastpluggy.core.tools.threads_tools import is_thread_alive, is_thread_alive_by_ident


@TaskWorker.register(name="watchdog.cleanup_stuck_tasks")
async def watchdog_cleanup_stuck_tasks():
    settings = TasksRunnerSettings()

    # Keep threshold for potential future use, but we will check all unfinished tasks
    timeout_minutes = settings.watchdog_timeout_minutes
    _threshold = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

    with session_scope() as session:
        # Look at tasks in DB and update status if the thread/pid is not present anymore
        result = session.execute(
            select(TaskReportDB)
            .where(TaskReportDB.finished == False)
        )
        pending_tasks = result.scalars().all()

        updated_dead = 0

        for task in pending_tasks:
            # Determine if associated execution context (thread) is still running
            native_id = task.thread_native_id
            ident = task.thread_ident

            # Convert to int if stored as text
            try:
                native_id_int = int(native_id) if native_id is not None else None
            except (TypeError, ValueError):
                native_id_int = None

            try:
                ident_int = int(ident) if ident is not None else None
            except (TypeError, ValueError):
                ident_int = None

            running_by_native = is_thread_alive(native_id_int) if native_id_int is not None else False
            running_by_ident = is_thread_alive_by_ident(ident_int) if ident_int is not None else False

            is_running = running_by_native or running_by_ident

            if not is_running:
                # Mark as DEAD since the underlying execution is no longer present
                task.status = TaskStatus.DEAD
                task.finished = True
                task.finished_at = datetime.now(timezone.utc)
                task.end_time = task.finished_at
                task.result = "Watchdog: execution context missing (thread/process not alive). Marked as DEAD."
                updated_dead += 1

                # TODO : remove the task_lock if pid is not running anymore
                #  -> maybe use notification system
                # await notify_task_event(...)

        session.commit()

    return f"{updated_dead} tasks marked as dead by watchdog."
