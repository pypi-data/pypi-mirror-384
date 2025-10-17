import json

from fastapi import Request, Depends, APIRouter
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.flash import FlashMessage
from fastpluggy.core.menu.decorator import menu_entry
from fastpluggy.core.tools.fastapi import redirect_to_previous
from fastpluggy.core.view_builer.components.table_model import TableModelView
from fastpluggy.core.widgets import AutoLinkWidget
from fastpluggy.core.widgets.categories.input.button_list import ButtonListWidget
from fastpluggy.core.widgets.categories.display.custom import CustomTemplateWidget
from fastpluggy.core.widgets.render_field_tools import RenderFieldTools
from ...config import TasksRunnerSettings
from ...persistence.models.scheduled import ScheduledTaskDB
from ...routers.schema import CreateScheduledTaskRequest, UpdateScheduledTaskRequest
from ...widgets.task_form import TaskFormView

front_schedule_task_router = APIRouter(
    prefix='/scheduled_task',
    tags=["task_router"],
)


@menu_entry(label="Scheduled List", icon='fa-solid fa-clock', )
@front_schedule_task_router.get("/", name="list_scheduled_tasks")
def list_scheduled_tasks(request: Request, view_builder=Depends(get_view_builder)):
    buttons = []
    settings = TasksRunnerSettings()
    if settings.allow_create_schedule_task:
        buttons.append(AutoLinkWidget(label="Create a Scheduled Task", route_name='create_scheduled_task', ))
    if settings.scheduler_enabled and settings.store_task_db:
            buttons.append(AutoLinkWidget(label='Scheduled Task Monitoring', route_name='scheduled_task_monitoring', icon="ti ti-activity"))
    items = [
        ButtonListWidget(
            buttons=buttons
        ),
        TableModelView(
            model=ScheduledTaskDB,
            title="Task scheduled",
            fields=[
                ScheduledTaskDB.name, ScheduledTaskDB.cron, ScheduledTaskDB.interval,
                #  ScheduledTaskDB.last_status,
                ScheduledTaskDB.is_late, ScheduledTaskDB.next_run, ScheduledTaskDB.last_attempt,
                ScheduledTaskDB.last_task_id, ScheduledTaskDB.enabled],
            links=[
                AutoLinkWidget(
                    label="View Last Task",
                    route_name="task_details",  # from your existing router
                    param_inputs={"task_id": '<last_task_id>'},
                    condition=lambda row: row['last_task_id'] is not None
                ),
                # TODO : add a retry button
                AutoLinkWidget(
                    label="Edit",
                    route_name="edit_scheduled_task",
                    param_inputs={"task_id": '<id>'},
                    css_class="btn btn-sm btn-primary"
                ),
            ],
            field_callbacks={
                ScheduledTaskDB.enabled: RenderFieldTools.render_boolean,
                ScheduledTaskDB.last_attempt: RenderFieldTools.render_datetime,
                ScheduledTaskDB.next_run: RenderFieldTools.render_datetime,
                ScheduledTaskDB.last_task_id: lambda
                    v: f'<a href="{request.url_for("task_details", task_id=v)}">{v}</a>' if v else '',
                ScheduledTaskDB.is_late: lambda
                    v: '<span class="badge bg-red">Yes</span>' if v else '<span class="badge bg-green">No</span>',

            },
            exclude_fields=[
                ScheduledTaskDB.created_at,
                ScheduledTaskDB.updated_at,
                ScheduledTaskDB.kwargs,
                ScheduledTaskDB.notify_on,
                ScheduledTaskDB.function,
            ]
        )
    ]

    return view_builder.generate(
        request,
        title="List of scheduled tasks",
        widgets=items
    )


@front_schedule_task_router.get("/create", name="create_scheduled_task")
def create_scheduled_task(
        request: Request,
        view_builder=Depends(get_view_builder)
):
    view = TaskFormView(
        title="New Scheduled Task",
        submit_url=str(request.url_for("create_scheduled_task_post")),
        url_after_submit=str(request.url_for("list_scheduled_tasks")),
        mode="schedule_task",
    )
    return view_builder.generate(request, widgets=[view])


@front_schedule_task_router.post("/create", name="create_scheduled_task_post")
def create_scheduled_task_post(
        request: Request,
        payload: CreateScheduledTaskRequest,
        method: str = 'web',
        db: Session = Depends(get_db)
):
    task = ScheduledTaskDB(
        name=payload.name,
        function=payload.function,
        cron=payload.cron,
        interval=payload.interval,
        kwargs=json.dumps(payload.kwargs),
        # notify_on disabled for now
        # notify_on=json.dumps(payload.notify_on),
        enabled=True,
    )
    db.add(task)
    db.commit()
    mesg = FlashMessage.add(request=request, message=f"Scheduled Task {payload.name} created !")

    if method == "web":
        return redirect_to_previous(request)
    else:
        return JSONResponse(content=mesg.to_dict())


@front_schedule_task_router.get("/edit/{task_id}", name="edit_scheduled_task")
def edit_scheduled_task(
        request: Request,
        task_id: int,
        view_builder=Depends(get_view_builder),
        db: Session = Depends(get_db)
):
    # Get the scheduled task from database
    task = db.query(ScheduledTaskDB).filter(ScheduledTaskDB.id == task_id).first()
    if not task:
        FlashMessage.add(request=request, message=f"Scheduled Task with ID {task_id} not found!", category="error")
        return redirect_to_previous(request)

    # Parse kwargs from JSON string
    kwargs_dict = {}
    if task.kwargs:
        try:
            kwargs_dict = json.loads(task.kwargs)
        except:
            kwargs_dict = {}

    # Prepare task data for the template
    task_data = {
        "id": task.id,
        "name": task.name,
        "function": task.function,
        "cron": task.cron,
        "interval": task.interval,
        "enabled": task.enabled,
        "allow_concurrent": task.allow_concurrent,
        "kwargs": json.dumps(kwargs_dict, indent=2),
        "last_attempt": task.last_attempt.strftime('%Y-%m-%d %H:%M:%S') if task.last_attempt else None,
        "last_task_id": task.last_task_id,
        "last_status": task.last_status
    }

    # Create custom template widget
    widget = CustomTemplateWidget(
        template_name="tasks_worker/scheduled_task_edit.html.j2",
        context={
            "task": task_data,
            "submit_url": str(request.url_for("edit_scheduled_task_post", task_id=task_id)),
            "cancel_url": str(request.url_for("list_scheduled_tasks"))
        }
    )

    return view_builder.generate(
        request,
        title=f"Edit Scheduled Task: {task.name}",
        widgets=[widget]
    )


@front_schedule_task_router.post("/edit/{task_id}", name="edit_scheduled_task_post")
def edit_scheduled_task_post(
        request: Request,
        task_id: int,
        payload: UpdateScheduledTaskRequest,
        method: str = 'web',
        db: Session = Depends(get_db)
):
    # Get the scheduled task from database
    task = db.query(ScheduledTaskDB).filter(ScheduledTaskDB.id == task_id).first()
    if not task:
        mesg = FlashMessage.add(request=request, message=f"Scheduled Task with ID {task_id} not found!", category="error")
        if method == "web":
            return redirect_to_previous(request)
        else:
            return JSONResponse(content=mesg.to_dict(), status_code=404)

    # Update only provided fields
    if payload.name is not None:
        task.name = payload.name
    if payload.function is not None:
        task.function = payload.function
    if payload.cron is not None:
        task.cron = payload.cron
    if payload.interval is not None:
        task.interval = payload.interval
    if payload.kwargs is not None:
        task.kwargs = json.dumps(payload.kwargs)
    if payload.enabled is not None:
        task.enabled = payload.enabled
    if payload.allow_concurrent is not None:
        task.allow_concurrent = payload.allow_concurrent

    db.commit()
    mesg = FlashMessage.add(request=request, message=f"Scheduled Task {task.name} updated successfully!")

    if method == "web":
        return redirect_to_previous(request)
    else:
        return JSONResponse(content=mesg.to_dict())
