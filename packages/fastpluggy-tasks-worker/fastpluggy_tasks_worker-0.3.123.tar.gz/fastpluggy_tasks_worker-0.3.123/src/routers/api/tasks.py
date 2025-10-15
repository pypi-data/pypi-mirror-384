import inspect

from fastapi import Request, APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from fastpluggy.core.database import get_db
from fastpluggy.core.tools.inspect_tools import process_function_parameters
from fastpluggy.fastpluggy import FastPluggy
from ..schema import CreateTaskRequest
from ...persistence.models.context import TaskContextDB
from ...persistence.repository.schedule_monitoring import FilterCriteria
from ...persistence.repository.tasks import get_task_context_reports_and_format
from ...registry.registry import task_registry

api_tasks_router = APIRouter(
    prefix='/api',
)


@api_tasks_router.get("/tasks", name="list_tasks")
async def list_tasks(
        db: Session = Depends(get_db),
        task_name: str = None,
        start_time: str = None,
        end_time: str = None
):
    # Create filter criteria with default date as today if not specified
    filter_criteria = FilterCriteria(
        task_name=task_name,
        start_time=start_time if start_time else "1d",  # Default to last 24 hours
        end_time=end_time if end_time else "now"  # Default to now
    )

    return get_task_context_reports_and_format(db, filter_criteria=filter_criteria)

@api_tasks_router.get("/task/{task_id}", name="get_task")
async def get_task(task_id: str, db: Session = Depends(get_db)):
    results = get_task_context_reports_and_format(db, task_id=task_id)
    if not results:
        return JSONResponse(status_code=404, content={"detail": "Task not found"})
    return results[0]


@api_tasks_router.post("/task/{task_id}/retry", name="retry_task")
def retry_task(task_id: str, request: Request, db=Depends(lambda: next(get_db()))):
    context = db.query(TaskContextDB).filter(TaskContextDB.task_id == task_id).first()
    if not context:
        raise HTTPException(status_code=404, detail="Task context not found")

    func = task_registry.get(context.func_name)
    if not func:
        raise HTTPException(status_code=400, detail="Function not found in registry")

    task_name =f"{context.task_name} (retry)" if "(retry)" not in context.task_name else context.task_name
    # Re-submit the task with parent_task_id
    from fastpluggy_plugin.tasks_worker import TaskWorker
    new_task_id = TaskWorker.submit(
        func,
        args=context.args,
        kwargs=context.kwargs,
        task_name=task_name,
        parent_task_id=task_id,
        task_origin="api-retry",
    )

    return {"task_id": new_task_id}



@api_tasks_router.post("/task/{task_id}/cancel", name="cancel_task")
async def cancel_task(task_id: str):
    """
    Cancel a running task by task_id and mark its status as 'manual_cancel'.
    """
    # Retrieve the global task runner instance.
    runner = FastPluggy.get_global("tasks_worker")
    if not runner:
        raise HTTPException(status_code=500, detail="Task runner is not available")

    # Attempt to cancel the running future.
    success = runner.cancel_task_with_notification(task_id)

    if not success:
        raise HTTPException(status_code=400, detail="Task not running or already finished")

    return {"task_id": task_id, "cancelled": success, "status": "manual_cancel"}

@api_tasks_router.post("/task/submit", name="submit_task")
async def submit_task(request: Request, payload: CreateTaskRequest ):
    from ...registry.registry import task_registry
    func = task_registry.get(payload.function)
    if not func:
        return JSONResponse({"error": f"Function {payload.function} not found"}, status_code=400)

    sig = inspect.signature(func)
    input_kwargs = payload.kwargs
    typed_kwargs = process_function_parameters(func_signature=sig, param_values=input_kwargs)

    from fastpluggy_plugin.tasks_worker import TaskWorker
    task_id = TaskWorker.submit(
        func,
        kwargs=typed_kwargs,
        task_name=payload.name or payload.function,
        topic=payload.topic,
        task_origin="api",
        max_retries=payload.max_retries,
        retry_delay=payload.retry_delay,
        allow_concurrent=payload.allow_concurrent,
    )

    return {"task_id": task_id}


