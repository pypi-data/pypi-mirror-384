"""
Celery compatibility layer entrypoints.
"""
import logging
from typing import Optional

from fastpluggy.core.plugin_state import PluginState
from fastpluggy.core.tools.install import is_installed


def init_celery_compat(settings, plugin: Optional[PluginState] = None):
    """
    Initialize Celery compatibility features by discovering Celery tasks and periodic schedule
    from a configured Celery application path (module:attr) if Celery is installed.
    """
    from .discovery import (
        discover_celery_tasks_from_app,
        discover_celery_periodic_tasks,
    )

    app_path = getattr(settings, "celery_app_path", None)
    if not app_path or ":" not in app_path:
        logging.warning(f"Celery app path '{app_path}' is not a valid 'module:app' path.")
        return

    if not is_installed("celery"):
        logging.warning("Celery is NOT installed. Skipping Celery compatibility init.")
        return

    try:
        discover_celery_tasks_from_app(app_path, plugin_state=plugin)
        discover_celery_periodic_tasks(app_path, plugin_state=plugin)
    except Exception as e:
        logging.warning(f"Error initializing Celery compatibility for '{app_path}': {e}")
