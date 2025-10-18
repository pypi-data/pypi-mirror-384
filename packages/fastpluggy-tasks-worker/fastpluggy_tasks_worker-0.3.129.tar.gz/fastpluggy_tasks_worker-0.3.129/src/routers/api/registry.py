from fastapi import APIRouter
from fastpluggy.core.tools.serialize_tools import serialize_value

api_registry_router = APIRouter(
    prefix='/api/registry',
)


@api_registry_router.get("/available", name="list_available_tasks")
def list_available_tasks():
    from ...registry.registry import task_registry
    meta = task_registry.list_metadata()
    meta = sorted(meta, key=lambda x: x.get("name", x.get("function")))
    meta = serialize_value(meta)
    return meta

