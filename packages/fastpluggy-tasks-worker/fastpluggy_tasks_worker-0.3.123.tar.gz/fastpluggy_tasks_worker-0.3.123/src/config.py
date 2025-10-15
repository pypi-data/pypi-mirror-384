from typing import Optional, List

from fastpluggy.core.config import BaseDatabaseSettings


class TasksRunnerSettings(BaseDatabaseSettings):
    """
    Settings for the tasks_worker plugin.
    Notes on currently unused settings (kept for future wiring/compatibility):
    - external_notification_loaders: Not used by current notifier flow (only referenced in old/ code).
    - watchdog_enabled / watchdog_timeout_minutes: Watchdog job is not currently scheduled; values are read by tasks/watchdog.py but not invoked at runtime.
    """

    BROKER_TYPE : str = 'local'  # Used by broker.factory.get_broker()

    # Topics
    default_topic: str = "default"  # Used as fallback topic for submissions and runner wiring

    # Executor settings
    #thread_pool_max_workers: Optional[int] = None  # None means use default (CPU count * 5). Not wired currently.

    # Scheduler
    scheduler_enabled: bool = True  # Controls enabling of scheduler routes and background loop
    scheduler_frequency: float = 5  # Used by tasks/scheduler main loop sleep
    allow_create_schedule_task: bool = True  # Controls UI ability to create scheduled tasks

    # notifier
    external_notification_loaders: Optional[List[str]] = []  # UNUSED in current implementation (legacy placeholder)

    # Registry/Discover of tasks
    enable_auto_task_discovery: bool = True  # Enables scanning for task functions in loaded modules

    # Celery
    discover_celery_tasks: bool = True  # Enables Celery task discovery integration
    celery_app_path: str = "myproject.worker:celery_app"  # Path to the Celery app object for discovery
    discover_celery_schedule_enabled_status: bool = False # Default enabled status when importing Celery beat schedule


    store_task_db: bool = True  # Controls DB persistence of task contexts/reports
    #store_task_notif_db: bool = False  # Not used currently

    # Purge in case the task is stored in DB
    purge_enabled :bool = True  # Enables purge job creation (if/when scheduled)
    purge_after_days: int = 30  # Retention period for purge job


    watchdog_enabled: bool = True  # UNUSED: watchdog task scheduling is commented out
    #watchdog_frequency: float = 5  # Not wired currently
    watchdog_timeout_minutes: int = 120  # UNUSED at runtime unless watchdog task is scheduled

# maybe add a module prefix
#    class Config:
#        env_prefix = "tasks_worker_"