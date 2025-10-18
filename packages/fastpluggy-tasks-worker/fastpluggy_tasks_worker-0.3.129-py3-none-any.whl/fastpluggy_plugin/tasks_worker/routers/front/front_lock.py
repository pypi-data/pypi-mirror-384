from fastapi import APIRouter, Request, Depends, HTTPException, Query
from starlette.responses import JSONResponse

from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.flash import FlashMessage
from fastpluggy.core.tools.fastapi import redirect_to_previous
from fastpluggy.core.widgets import AutoLinkWidget, TableWidget
from fastpluggy.core.widgets.categories.input.button_list import ButtonListWidget
from ... import TaskWorker

front_task_lock_router = APIRouter(tags=["task_locks"])


@front_task_lock_router.get("/task_locks", name="view_task_locks")
def view_task_locks(request: Request, view_builder=Depends(get_view_builder)):
    broker = TaskWorker._get_broker()
    locks = broker.get_locks() if hasattr(broker, "get_locks") else []

    # Directly pass LockInfo objects to the TableView; it can handle plain objects with __dict__
    items = [
        ButtonListWidget(buttons=[
            AutoLinkWidget(label="Back to Task Dashboard", route_name="dashboard_tasks_worker"),
        ]),
        TableWidget(
            title="Current Task Locks",
            data=locks,
            fields=["task_id", "task_name", "acquired_at", "locked_by"],
            headers={
                "task_id": "Task ID",
                "task_name": "Task Name",
                "acquired_at": "Acquired At",
                "locked_by": "Locked By"
            },
            links=[
                AutoLinkWidget(
                    label="Force Release",
                    route_name="force_release_task_lock",
                    param_inputs={"task_id": "<task_id>", 'method': 'web'}
                )
            ]
        )
    ]
    return view_builder.generate(request, widgets=items, title="Task Locks")


@front_task_lock_router.get("/task_locks/release", name="force_release_task_lock")
def force_release_task_lock(
        request: Request,
        task_id: str = Query(...),
        method: str = 'web',
):
    broker = TaskWorker._get_broker()
    ok = broker.force_release_lock(task_id) if hasattr(broker, "force_release_lock") else False
    if not ok:
        raise HTTPException(status_code=404, detail="Lock not found")
    message = f"Lock on '{task_id}' released" if ok else f"Lock on '{task_id}' not released"

    mesg = FlashMessage.add(request=request, message=message)

    if method == "web":
        return redirect_to_previous(request)
    else:
        return JSONResponse(content=mesg.to_dict())
