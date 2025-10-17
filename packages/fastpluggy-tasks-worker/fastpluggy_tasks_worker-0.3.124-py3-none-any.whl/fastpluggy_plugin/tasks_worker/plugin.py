# plugin.py
from typing import Annotated, Any

from fastpluggy.core.menu.schema import MenuItem
from fastpluggy.core.module_base import FastPluggyBaseModule
from fastpluggy.core.plugin_state import PluginState
from fastpluggy.core.tools.inspect_tools import InjectDependency
from .config import TasksRunnerSettings


def get_router():
#    from .routers.api.notifier import api_notifier_router
    from .routers.api.registry import api_registry_router
    from .routers.api.tasks import api_tasks_router
    from .routers.api.broker import api_broker_router
    from .routers.front.front_lock import front_task_lock_router
    #from .routers.front.front_notifier import front_notifier_router
    from .routers.front.front_tasks import front_task_router
    from .routers.front.front_debug import front_task_debug_router
    from .routers.monitoring.task_duration import monitoring_task_duration

    routers = [
       # api_notifier_router,
        api_registry_router,
        api_tasks_router,
        api_broker_router,
        front_task_lock_router,
      #  front_notifier_router,
        front_task_router,
        front_task_debug_router,
        monitoring_task_duration,
    ]
    settings: TasksRunnerSettings = TasksRunnerSettings()
    if settings.discover_celery_tasks:
        from .celery_compat.router import celery_router
        routers.append(celery_router)

    if settings.scheduler_enabled:
        from .scheduler.routers.front_schedule import front_schedule_task_router
        routers.append(front_schedule_task_router)

        if settings.scheduler_enabled and settings.store_task_db:
            from .scheduler.routers.monitoring import scheduled_tasks_monitoring_router
            routers.append(scheduled_tasks_monitoring_router)

    return routers


class TaskRunnerPlugin(FastPluggyBaseModule):
    module_name: str = "tasks_worker"

    module_menu_name: str = "Task Runner"
    module_menu_type: str = "main"

    module_settings: Any = TasksRunnerSettings
    module_router: Any = get_router

    extra_js_files: list = []

    depends_on: dict = {
        "crud_tools": ">=0.0.2",
    }

    optional_dependencies: dict = {
        "websocket_tool": ">=0.1.0",
        "ui_tools": ">=0.0.2",
    }

    extra_js_files: list = ['/app_static/tasks_worker/js/tasks.js']

    def after_setup_templates(self, fast_pluggy: Annotated["FastPluggy", InjectDependency]) -> None:
        """
        Add global Jinja template variable for the API URL to trigger tasks.
        """
        # Add URL for task submission endpoint to global Jinja templates
        task_submit_url=fast_pluggy.app.url_path_for("submit_task")
        fast_pluggy.templates.env.globals["task_submit_url"] = task_submit_url
        from fastpluggy.fastpluggy import FastPluggy
        FastPluggy.extend_globals('js_global_var', {'task_submit_url': task_submit_url})

    def on_load_complete(
            self,
            fast_pluggy: Annotated["FastPluggy", InjectDependency],
            plugin: Annotated["PluginState", InjectDependency],
    ) -> None:
        # Add UI menu entries
        fast_pluggy.menu_manager.add_parent_item(
            menu_type='main',
            item=MenuItem(label="Task Runner", icon="fa-solid fa-gears", parent_name=self.module_name)
        )


        # Initialize worker (ensures broker is ready)
        from . import TaskWorker
        TaskWorker.init_worker(fast_pluggy=fast_pluggy)


    #    # # Register default notifiers
    # from .notifiers.registry import setup_default_notifiers
    # from .notifiers.loader import load_external_notification_config_from_settings
    #
    # setup_default_notifiers()
    # load_external_notification_config_from_settings()
    #
    # # Setup scheduled maintenance tasks
    # if settings.store_task_db:
    #     with session_scope() as db:
    #         from .repository.scheduled import ensure_scheduled_task_exists
    #
    #         if settings.purge_enabled:
    #             from .tasks.maintenance import purge_old_tasks
    #             ensure_scheduled_task_exists(
    #                 db=db,
    #                 function=purge_old_tasks,
    #                 task_name="purge_old_tasks",
    #                 cron="0 4 * * *",  # Every day at 4am
    #             )
    #
    #         # if settings.watchdog_enabled:
    #         # todo : move to worker class to ensure all is always sync
    #         #    from .tasks.watchdog import watchdog_cleanup_stuck_tasks
    #         #    ensure_scheduled_task_exists(
    #         #        db=db,
    #         #        function=watchdog_cleanup_stuck_tasks,
    #         #        task_name="watchdog_cleanup_stuck_tasks",
    #         #        interval=15,  # Every 15 minutes
    #         #    )
    #

        from .metrics import register_broker_collector_once
        register_broker_collector_once()
