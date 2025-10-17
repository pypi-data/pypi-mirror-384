from fastapi import APIRouter, Request, Depends

from fastpluggy.core.auth import require_authentication
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets.categories.data.debug import DebugView
from ..config import TasksRunnerSettings
from .discovery import discover_celery_periodic_tasks
from .discovery import discover_celery_tasks_from_app


celery_router = APIRouter(
    prefix="/celery",
    tags=["celery"],
    dependencies=[Depends(require_authentication)],
)


@celery_router.get("/celery_list_tasks", name="celery_list_tasks")
async def celery_list_tasks(
        request: Request,
        view_builder=Depends(get_view_builder)
):
    settings = TasksRunnerSettings()
    data = discover_celery_tasks_from_app(settings.celery_app_path)
    schedule = discover_celery_periodic_tasks(settings.celery_app_path)

    return view_builder.generate(
        request,
        title="Celery list",
        items=[
            DebugView(data=data, title="Celery Tasks"),
            DebugView(data=schedule, title="Celery Scheduled Tasks"),
        ]
    )

