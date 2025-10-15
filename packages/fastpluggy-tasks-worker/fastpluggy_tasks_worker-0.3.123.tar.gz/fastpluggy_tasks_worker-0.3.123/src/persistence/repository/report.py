import datetime

from fastpluggy.core.database import session_scope
from fastpluggy.core.tools.serialize_tools import serialize_value
from fastpluggy.core.tools.threads_tools import get_tid, get_py_ident
from ..models.report import TaskReportDB
from ..schema.report import TaskReport
from ...core.status import TaskStatus


def init_report_from_context(context: "TaskContext") -> TaskReport:
    """
    Create and persist an initial TaskReport based on the context.
    """
    report = TaskReport(
        task_id=context.task_id,
        function=context.func_name,
        args=[str(a) for a in context.args],
        kwargs={k: str(v) for k, v in context.kwargs.items()},
        start_time=datetime.datetime.now(datetime.UTC),
        status=TaskStatus.RUNNING,
        thread_native_id=get_tid(),
        thread_ident=get_py_ident(),
    )
    return report


def save_report(report: TaskReport) -> None:
    """
    Persist the initial TaskReport before execution.
    """
    with session_scope() as db:
        data = TaskReportDB(**report.to_dict())
        db.add(data)
        db.commit()


def update_report(report: TaskReport) -> None:
    """
    Update fields on an existing TaskReportDB and in-memory TaskReport.
    - Preserves original start_time if already set in DB.
    - Computes duration when both start_time and end_time are available.
    """

    with session_scope() as db:
        exists = db.query(TaskReportDB).filter(TaskReportDB.task_id == report.task_id).first()
        if not exists:
            return

        data = report.to_dict()

        if 'result' in data:
            data['result'] = str(serialize_value(data['result']))

        # Preserve earliest start_time if already recorded
        if getattr(exists, 'start_time', None):
            data.pop('start_time', None)

        # Apply updates except duration (we'll compute it afterward)
        for key, value in data.items():
            if hasattr(exists, key):
                setattr(exists, key, value)

        # Compute duration if possible
        start_time = exists.start_time or data.get('start_time')
        end_time = exists.end_time or data.get('end_time')
        try:
            if start_time and end_time:
                exists.duration = (end_time - start_time).total_seconds()
        except Exception:
            # leave duration as-is on error
            pass

        db.add(exists)
        db.commit()
        db.refresh(exists)
        return exists
