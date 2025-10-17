import logging

from fastapi import Request, Depends, APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.menu.decorator import menu_entry
from fastpluggy.core.widgets import CustomTemplateWidget, AutoLinkWidget
from fastpluggy.core.widgets.categories.data.debug import DebugView
from fastpluggy.core.widgets.categories.input.button_list import ButtonListWidget
from ...broker.factory import get_broker
from ...persistence.models.context import TaskContextDB
from ...persistence.models.report import TaskReportDB
from ...widgets.task_form import TaskFormView

front_task_router = APIRouter(
    tags=["task_router"],
)

@menu_entry( label="Dashboard",   icon='fa fa-list',position=0)
@front_task_router.get("/", response_class=HTMLResponse, name="dashboard_tasks_worker")
async def dashboard(request: Request, view_builder=Depends(get_view_builder), ):
    return view_builder.generate(
        request,
        title="List of tasks",
        widgets=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Run a Task", route_name="run_task_form"),
                AutoLinkWidget(label="See Lock Tasks", route_name="view_task_locks"),
                AutoLinkWidget(label="See Running Tasks", route_name="list_running_tasks"),
                #AutoLinkWidget(label="See notifier", route_name="view_notifier"),
                AutoLinkWidget(label="Task Duration Analytics", route_name="task_duration_analytics"),
                AutoLinkWidget(label="Scheduled Task Monitoring", route_name="scheduled_task_monitoring"),
                AutoLinkWidget(label="Broker info", route_name="broker_debug_dashboard"),
            ]),
            CustomTemplateWidget(
                template_name="tasks_worker/dashboard.html.j2",
                context={
                    "request": request,
                    "url_submit_task": request.url_for("submit_task"),
                    "url_list_tasks": request.url_for("list_tasks"),
                    "url_detail_task": request.url_for("task_details", task_id="TASK_ID_REPLACE"),
                    "url_get_task": request.url_for("get_task", task_id="TASK_ID_REPLACE"),
                    "url_broker_cluster": request.url_for("broker_cluster_stats"),
                    "url_broker_workers": request.url_for("broker_workers"),
                    # "ws_logs_url": f"ws://{request.client.host}:{request.url.port or 80}" + request.url_for(
                    #    "stream_logs", task_id="TASK_ID_REPLACE").path
                }
            ),
        ]
    )
    # TODO : add a retry button


@front_task_router.get("/task/{task_id}/details", name="task_details")
def task_details(
        request: Request,
        task_id: str,
        view_builder=Depends(get_view_builder),
        db=Depends(lambda: next(get_db())),
):
    task_context = db.query(TaskContextDB).filter(TaskContextDB.task_id == task_id).first()
    if not task_context:
        return view_builder.generate(request, title="Task not found", items=[
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Return to list", route_name="dashboard_tasks_worker"),
            ])
        ])

    task_report = db.query(TaskReportDB).filter(TaskReportDB.task_id == task_id).first()

    # Fetch child tasks (if any) and their reports
    child_tasks = []
    children_ctx = db.query(TaskContextDB).filter(TaskContextDB.parent_task_id == task_id).all()
    if children_ctx:
        child_ids = [c.task_id for c in children_ctx]
        reports = db.query(TaskReportDB).filter(TaskReportDB.task_id.in_(child_ids)).all()
        report_map = {r.task_id: r for r in reports}
        for c in children_ctx:
            r = report_map.get(c.task_id)
            child_tasks.append({
                "task_id": c.task_id,
                "task_name": c.task_name,
                "status": getattr(r, "status", None),
                "start_time": getattr(r, "start_time", None),
                "end_time": getattr(r, "end_time", None),
                "duration": getattr(r, "duration", None),
            })

    items = [
        CustomTemplateWidget(
            template_name='tasks_worker/task_details.html.j2',
            context={
                "request": request,
                "task_context": task_context,
                "task_report": task_report,
                "child_tasks": child_tasks,
                "url_retry_task": request.url_for("retry_task", task_id=task_id),
                "url_detail_task": request.url_for("task_details", task_id="TASK_ID_REPLACE"),
                "url_task_graph": request.url_for("tasks_graph", task_id="TASK_ID_REPLACE"),
            }
        ),

        ButtonListWidget(buttons=[
            AutoLinkWidget(label="Return to task list", route_name="dashboard_tasks_worker"),
        ])
    ]

    return view_builder.generate(
        request,
        title=f"Task {task_id} overview",
        widgets=items
    )

@menu_entry(label="Create Task ",  icon='fa fa-plus',)
@front_task_router.get("/run_task", name="run_task_form")
def run_task_form(request: Request, view_builder=Depends(get_view_builder), ):
    return view_builder.generate(
        request,
        title="Run a Task",
        widgets=[
            TaskFormView(
                title="Run a Task",
                submit_url=str(request.url_for("submit_task")),
                mode="create_task",
            )
        ]
    )

@menu_entry(label="Task Running", icon="fa-solid fa-rotate")
@front_task_router.get("/running_tasks", name="list_running_tasks")
def list_running_tasks(request: Request, view_builder=Depends(get_view_builder), db: Session = Depends(get_db)):
    """
    Show currently running tasks using the broker (preferred source of truth).
    We query the broker for active tasks (in-flight) on the default topic and
    render them. If the broker is unavailable, we fall back to DB-based view.
    """
    # Try broker first
    task_data = []
    running_tasks_count = 0
    try:
        broker = get_broker()
        active = broker.get_all_active_tasks(None) or []

        # Show all tasks returned by the broker (no state filtering)
        running_tasks_count = len(active)

        # Optionally enrich with DB context if present
        # Collect task_ids present in payloads
        payload_ids = []
        for t in active:
            payload = getattr(t, "payload", None) or {}
            tid = payload.get("task_id") or getattr(t, "id", None)
            if tid:
                payload_ids.append(tid)

        ctx_map = {}
        if payload_ids:
            contexts = db.query(TaskContextDB).filter(TaskContextDB.task_id.in_(payload_ids)).all()
            ctx_map = {c.task_id: c for c in contexts}

        # Build UI rows
        for t in active:
            payload = getattr(t, "payload", None) or {}
            headers = getattr(t, "headers", None) or {}
            created_at = getattr(t, "created_at", None)
            # created_at may be datetime or string; map to ISO string if possible
            try:
                start_iso = created_at.isoformat() if hasattr(created_at, "isoformat") else (str(created_at) if created_at else None)
            except Exception:
                start_iso = str(created_at) if created_at else None

            task_id = payload.get("task_id") or getattr(t, "id", None)
            ctx = ctx_map.get(task_id)

            task_info = {
                "task_id": task_id,
                "status": getattr(t, "state", None) or "running",
                "task_name": payload.get("task_name") or (ctx.task_name if ctx else "Unknown"),
                "args": payload.get("args") if payload.get("args") is not None else (ctx.args if ctx else "[]"),
                "kwargs": payload.get("kwargs") if payload.get("kwargs") is not None else (ctx.kwargs if ctx else "{}"),
                "start_time": start_iso,
                "end_time": None,
                "duration": None,  # Unknown at broker level
                "worker_id": headers.get("worker_id") if isinstance(headers, dict) else None,
            }
            task_data.append(task_info)

        logging.info(f"Broker running task_data: {task_data}")

    except Exception as e:
        logging.warning(f"Broker unavailable for running tasks, falling back to DB. Error: {e}")
        # Fallback to previous DB-based logic
        q = db.query(TaskReportDB)
        reports = q.all()
        task_ids = [r.task_id for r in reports]
        running_tasks_count = len(task_ids)
        task_contexts = db.query(TaskContextDB).filter(TaskContextDB.task_id.in_(task_ids)).all() if task_ids else []
        task_context_map = {context.task_id: context for context in task_contexts}
        report_map = {r.task_id: r for r in reports}
        for task_id in task_ids:
            rep = report_map.get(task_id)
            status = rep.status if rep and rep.status else "running"
            task_info = {
                "task_id": task_id,
                "status": status,
                "task_name": "Unknown",
                "args": "[]",
                "kwargs": "{}",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "worker_id": None,
            }
            ctx = task_context_map.get(task_id)
            if ctx:
                task_info["task_name"] = ctx.task_name
                task_info["args"] = ctx.args
                task_info["kwargs"] = ctx.kwargs
            if rep:
                try:
                    task_info["start_time"] = rep.start_time.isoformat() if rep.start_time else None
                except Exception:
                    task_info["start_time"] = str(rep.start_time) if rep.start_time else None
                try:
                    task_info["end_time"] = rep.end_time.isoformat() if rep.end_time else None
                except Exception:
                    task_info["end_time"] = str(rep.end_time) if rep.end_time else None
                task_info["duration"] = float(rep.duration) if rep.duration is not None else None
                task_info["worker_id"] = getattr(rep, "worker_id", None)
            task_data.append(task_info)

    logging.info(f"task_data: {task_data}")

    return view_builder.generate(
        request,
        title="Running Tasks",
        widgets=[
            CustomTemplateWidget(
                template_name="tasks_worker/running_tasks.html.j2",
                context={
                    "running_tasks_count": running_tasks_count,
                    "task_data": task_data,
                }
            ),
            DebugView(data=task_data, collapsed=True)
        ]
    )


@front_task_router.get("/task/{task_id}/graph", response_class=HTMLResponse)
async def tasks_graph(request: Request, task_id: str, db: Session = Depends(get_db),
                      view_builder=Depends(get_view_builder)):
    """
    Interactive graph of tasks linked to the given task_id, including ancestors and descendants.
    Node color: green=success, red=failed, default=blue; bold border for the current task.
    Hover over a node to see its direct parents and children. Click to open details.
    """
    # Verify starting task exists
    start = db.query(TaskContextDB).filter_by(task_id=task_id).first()
    if not start:
        raise HTTPException(404, "Task not found")

    # 2. BFS for ancestors & descendants (same logic as before)
    node_objs = {task_id: start}
    edges = []

    # Descendants
    dq, seen = [task_id], set()
    while dq:
        cur = dq.pop(0)
        if cur in seen: continue
        seen.add(cur)
        for child in db.query(TaskContextDB).filter_by(parent_task_id=cur):
            node_objs.setdefault(child.task_id, child)
            edges.append((cur, child.task_id))
            dq.append(child.task_id)

    # Ancestors
    aq, seen = [task_id], set()
    while aq:
        cur = aq.pop(0)
        if cur in seen: continue
        seen.add(cur)
        parent_id = node_objs[cur].parent_task_id
        if parent_id:
            parent = db.query(TaskContextDB).filter_by(task_id=parent_id).first()
            if parent:
                node_objs.setdefault(parent_id, parent)
                edges.append((parent_id, cur))
                aq.append(parent_id)

    # 3. Build maps for tooltip info
    parents_map = {tid: [] for tid in node_objs}
    children_map = {tid: [] for tid in node_objs}
    for p, c in edges:
        parents_map[c].append(p)
        children_map[p].append(c)

    # 5. Fetch statuses in bulk from TaskReportDB
    task_ids = list(node_objs.keys())
    reports = (
        db.query(TaskReportDB)
        .filter(TaskReportDB.task_id.in_(task_ids))
        .all()
    )
    # Map each task_id → its latest status (or None)
    status_map = {r.task_id: r.status for r in reports}
    duration_map = {r.task_id: r.duration for r in reports}

    # 6. Serialize nodes + edges for Jinja
    nodes = []
    for tid, task in node_objs.items():
        nodes.append({
            "id": tid,
            "label": task.task_name,
            "info": {
                "parents": parents_map[tid],
                "children": children_map[tid],
                "status": status_map.get(tid),
                "duration": duration_map.get(tid),
                "worker": "worker-01"
            },
            "is_root": tid == task_id,
            "detail_url": str(request.url_for("task_details", task_id=tid)),
        })

    edges_js = [{"source": p, "target": c} for p, c in edges]

    return view_builder.generate(
        request,
        title=f"Task Graph dependency : {task_id}",
        widgets=[
            CustomTemplateWidget(
                template_name="tasks_worker/graph.html.j2",
                context={
                    "nodes_json": nodes,
                    "edges_json": edges_js,
                })
        ])
