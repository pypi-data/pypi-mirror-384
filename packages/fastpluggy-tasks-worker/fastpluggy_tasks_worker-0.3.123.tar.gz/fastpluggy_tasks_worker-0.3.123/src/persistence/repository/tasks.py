from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..models.report import TaskReportDB
from ...persistence.models.context import TaskContextDB


from sqlalchemy import and_, or_, true
from sqlalchemy.orm import aliased

def get_task_context_and_repport(
    db: Session,
    task_id: str = None,
    limit: int = 20,
    filter_criteria=None,
):
    """
    Returns (TaskContextDB, TaskReportDB?) rows.
    - If a task has no report, TaskReportDB will be None.
    - Only the latest report per task is joined (good for perf and avoids duplicates).
    - If start_time/end_time filters are provided, contexts with no report are still included.
    """

    # Base: we first pick the contexts we want (so LIMIT applies to contexts)
    base_q = db.query(TaskContextDB)

    if task_id:
        base_q = base_q.filter(TaskContextDB.task_id == task_id)

    # Order contexts (so LIMIT is deterministic)
    base_q = base_q.order_by(desc(TaskContextDB.id)).limit(limit).subquery()
    Ctx = aliased(TaskContextDB, base_q)

    # Correlated subquery: latest report per task (by start_time desc, then id desc)
    latest_report_subq = (
        db.query(TaskReportDB)
        .filter(TaskReportDB.task_id == Ctx.task_id)
        .order_by(
            TaskReportDB.start_time.desc().nullslast(),
            TaskReportDB.id.desc()
        )
        .limit(1)
        .correlate(Ctx)   # important for correlation with outer query
        .subquery()
    )
    LatestReport = aliased(TaskReportDB, latest_report_subq)

    # Now build the final query: contexts + (optional) latest report
    query = db.query(Ctx, LatestReport).outerjoin(LatestReport, true())

    # Optional filters
    if not task_id and filter_criteria:
        # Task name filter (on contexts)
        if getattr(filter_criteria, "task_name", None):
            query = query.filter(Ctx.task_name.ilike(f"%{filter_criteria.task_name}%"))

        # Time range filters (on the latest report), but keep contexts with no report
        start_time = getattr(filter_criteria, "start_time", None)
        end_time = getattr(filter_criteria, "end_time", None)

        if start_time and end_time:
            query = query.filter(
                or_(
                    LatestReport.start_time == None,
                    and_(LatestReport.start_time >= start_time,
                         LatestReport.start_time <= end_time),
                )
            )
        elif start_time:
            query = query.filter(
                or_(LatestReport.start_time == None,
                    LatestReport.start_time >= start_time)
            )
        elif end_time:
            query = query.filter(
                or_(LatestReport.start_time == None,
                    LatestReport.start_time <= end_time)
            )

    rows = query.all()
    return rows


def get_task_context_reports_and_format(db: Session, task_id: str = None, limit: int = 20, filter_criteria=None):
    rows = get_task_context_and_repport(db=db, task_id=task_id, limit=limit, filter_criteria=filter_criteria)

    return [
        {
            "task_id": context.task_id,
            "task_name": context.task_name,
            "function": context.func_name,
            "args": context.args,
            "kwargs": context.kwargs,
            "notifier_config": context.notifier_config,
            "result": report.result if report else None,
            "logs": report.logs if report else None,
            "duration": report.duration if report else None,
            "error": report.error if report else None,
            "tracebacks": report.tracebacks if report else None,
            "attempts": report.attempts if report else None,
            "success": report.success if report else None,
            "status": report.status if report else None,
            "start_time": report.start_time.isoformat() if report and report.start_time else None,
            "end_time": report.end_time.isoformat() if report and report.end_time else None,
        }
        for context, report in rows
    ]

