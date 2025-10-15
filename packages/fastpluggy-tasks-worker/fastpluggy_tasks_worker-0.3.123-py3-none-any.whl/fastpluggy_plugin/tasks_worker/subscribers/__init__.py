import logging

from .telemetry import TaskTelemetry
from ..config import TasksRunnerSettings

from .db_adapter import DBPersistence
from .metrics import MetricsPersistence

def setup_persistance(bus):
    # Create and register persistence listener
    settings = TasksRunnerSettings()

    # Always register metrics persistence (no-op if prometheus_client missing)
    try:
        bus.subscribe_class(MetricsPersistence)
    except Exception as e:
        logging.exception(f"Failed to register metrics persistence: {e}")

    # Always register in-memory telemetry (very cheap, no deps)
    try:
            bus.subscribe_class(TaskTelemetry)
    except Exception as e:
            logging.exception(f"Failed to register task telemetry: {e}")

    if settings.store_task_db:
        from fastpluggy.core.database import create_table_if_not_exist

        from ..persistence.models.context import TaskContextDB
        create_table_if_not_exist(TaskContextDB)
        from ..persistence.models.report import TaskReportDB
        create_table_if_not_exist(TaskReportDB)

        if settings.scheduler_enabled:
            from ..persistence.models.scheduled import ScheduledTaskDB
            create_table_if_not_exist(ScheduledTaskDB)

        # if settings.store_task_notif_db:
        #     from ..models.notification import TaskNotificationDB
        #     create_table_if_not_exist(TaskNotificationDB)

        bus.subscribe_class(DBPersistence)  # auto-wires all on_<status> methods


    # Optionally return the bus for wiring
    return bus