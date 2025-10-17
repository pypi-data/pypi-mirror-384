import importlib
from types import MethodType
from typing import Any

from loguru import logger

from fastpluggy.core.plugin_state import PluginState
from .. import TaskWorker
from ..registry.registry import task_registry
from ..registry.utils import _unwrap, merge_task_metadata


# --------------------------------------------------------------------
# Celery Task Discovery
# --------------------------------------------------------------------

def discover_celery_tasks_from_app(app_path: str, plugin_state: PluginState = None ) -> list[dict[str, Any]]:
    """
    Discover Celery tasks from a Celery app URI ("module:app").
    Skips internal Celery tasks and already-registered functions.
    Returns details of newly discovered tasks.
    """
    discovered_details: list[dict[str, Any]] = []

    try:
        module_path, app_attr = app_path.rsplit(":", 1)
        module = importlib.import_module(module_path)
        celery_app = getattr(module, app_attr)
    except Exception as e:
        logger.warning(f"Failed to load Celery app from {app_path}: {e}")
        if plugin_state:
            plugin_state.warning.append(f"Failed to load Celery app from {app_path}: {e}")
        return discovered_details

    logger.info(f"📦 Discovering Celery tasks from app: {app_path}")
    # ─── Monkey-patch send_task ────────────────────────────────────────────────
    _orig_send = celery_app.send_task

    def _patched_send_task(self, name, args=None, kwargs=None, **options):
        logger.debug(f"[patched] send_task→ {name!r} args={args!r} kwargs={kwargs!r} options={options!r}")
        # todo : handle options here… like queue
        func = task_registry.get_by_fullname(name)
        if not func:
            logger.warning(f"[CELERY:_patched_send_task] Function not found: {name}")

        from .. import TaskWorker
        task_id = TaskWorker.submit(
            func,
            task_origin="celery_patched_send_task",
            kwargs=kwargs,
            args=args,
            #**options
        )
        logger.info(f"Function '{func}' scheduled as task with task_id: {task_id}")

        # return same format than celery
        from ..celery_compat.dummy import DummyAsyncResult
        return DummyAsyncResult(task_id)

    celery_app.send_task = MethodType(_patched_send_task, celery_app)
    # ──────────────────────────────────────────────────────────────────────────

    for task_name, task_obj in celery_app.tasks.items():
        try:
            if task_name.startswith("celery.") or not hasattr(task_obj, "run"):
                continue

            # skip anything we've already registered by name
            if task_registry.get(task_name) is not None:
                logger.warning(f"Skipping already-registered task '{task_name}' from {app_path}...")
                continue
            real_fn = _unwrap(task_obj.run)

            logger.info(f"✅ Found Celery task: {task_name}")

            # Register the task (annotates metadata on the unwrapped function)
            TaskWorker.register(
                name=task_name,
                description=f"Imported Celery task: {task_name}",
                tags=["celery", "external"],
                task_type="celery",
                allow_concurrent=True,
            )(real_fn)

            # Record detail for returned summary
            discovered_details.append({
                "task_name": task_name,
                "discovered_from": app_path,
                "module": real_fn.__module__,
                "qualified_name": real_fn.__qualname__,
            })
            merge_task_metadata(task_obj, discovery_method="discover_celery_tasks_from_app")
        except Exception as e:
            logger.exception(f"Failed to discover Celery task '{task_name}' from {app_path}: {e}")
            if plugin_state:
                plugin_state.warning.append(f"Failed to load Celery app from {app_path}: {e}")
            continue

    logger.info(f"🎯 {len(discovered_details)} Celery task(s) registered.")
    return discovered_details


def discover_celery_periodic_tasks(app_path: str, plugin_state: PluginState = None ):
    """
    Finds all entries in app.conf.beat_schedule and registers them in task_registry.
    """
    try:
        # Load the Celery app
        module_path, app_attr = app_path.rsplit(":", 1)
        module = importlib.import_module(module_path)
        celery_app = getattr(module, app_attr)
        celery_app.loader.import_default_modules()
    except Exception as e:
        logger.warning(f"Failed to load Celery app from {app_path}: {e}")
        if plugin_state:
            plugin_state.warning.append(f"Failed to load Celery app from {app_path}: {e}")
        return []

    # 2) create and send through our dummy
    from ..celery_compat.beat_capture import DummySender
    dummy = DummySender()
    celery_app.on_after_configure.send(sender=dummy)

    # 3) dummy.entries now holds everything that would have gone into beat_schedule
    return dummy.entries