import contextvars
import logging
import uuid
from typing import Optional, Tuple, Dict, Any

from fastpluggy.core.database import session_scope
from .broker.contracts import Broker
from .plugin import TaskRunnerPlugin

# from .progress import task_progress

current_task_ctx = contextvars.ContextVar(
    "current_task_ctx", default=None
)

# task_context_var.py (continued)
from contextlib import contextmanager


@contextmanager
def set_current_task_ctx(ctx):
    token = current_task_ctx.set(ctx)
    try:
        yield
    finally:
        current_task_ctx.reset(token)


class TaskWorker:
    _broker: Optional[Broker] = None

    @classmethod
    def _get_broker(cls) -> Broker:
        from .broker.factory import get_broker
        if cls._broker is None:
            cls._broker = get_broker()
        return cls._broker

    @staticmethod
    def register(
            name: str = None,
            description: str = "",
            tags: list[str] = None,
            schedule: str = None,
            max_retries: int = 0,
            allow_concurrent: bool = True,
            task_type: str = "native",
            topic: Optional[str] = None,
            **extra: Any,
    ):
        """
        Public wrapper around task_registry.register to decorate a function as a task.
        Mirrors TaskRegistry.register signature.
        """
        from .registry.registry import task_registry

        return task_registry.register(
            name=name,
            description=description,
            tags=tags,
            schedule=schedule,
            max_retries=max_retries,
            allow_concurrent=allow_concurrent,
            task_type=task_type,
            topic=topic,
            **extra,
        )

    @staticmethod
    def submit(
            func,
            args: Optional[Tuple] = None,
            kwargs: Optional[dict] = None,
            task_name: Optional[str] = None,
            topic: Optional[str] = None,
            max_retries: int = 0,
            retry_delay: int = 0,
            parent_task_id: Optional[str] = None,
            task_origin: str = "unk",
            allow_concurrent: Optional[bool] = None,
            extra_context: Optional[dict] = None,
            headers: Optional[Dict[str, Any]] = None,
    ):
        from .core.utils import it_allow_concurrent, func_to_path
        from .core.context import TaskContext

        # inherit parent task if we're inside one
        ctx_parent = current_task_ctx.get()
        if ctx_parent and not parent_task_id:
            parent_task_id = ctx_parent.task_id

        # Determine concurrency setting from function metadata if not explicitly provided
        if allow_concurrent is None:
            allow_concurrent = it_allow_concurrent(func)

        # Resolve default topic from registry metadata or settings if none provided
        if not topic:
            from .core.topic import resolve_topic
            topic = resolve_topic(func, topic)

        context = TaskContext(
            task_id=str(uuid.uuid4()),
            task_name=task_name or getattr(func, "__name__", "anonymous"),
            func_name=func_to_path(func) if not isinstance(func, str) else func,
            args=list(args or ()),
            kwargs=dict(kwargs or {}),
            # notifier_config=notify_config or [],
            parent_task_id=parent_task_id,
            max_retries=max_retries,
            retry_delay=retry_delay,
            task_origin=task_origin,
            topic=topic,
            allow_concurrent=allow_concurrent,
            extra_context=extra_context or {},
        )

        # TODO: Persist context replace with event
        # self.bus.emit(TaskLifecycleEvent(
        #                 status=TaskStatus.CREATED,
        #                 task_id=ctx.task_id,
        #                 context=ctx,
        #                 broker_msg_id=msg.id,
        #             ))
        try:
            # Temporary direct persistence; later this will emit CREATED event to a shared bus
            from .persistence.repository.context import save_context
            save_context(context)
        except Exception as e:
            # Avoid breaking submission if persistence fails
            logging.exception(f"Error on save in database the task : {e}")

        broker = TaskWorker._get_broker()

        # Ensure the topic exists on the broker (no-op for brokers that auto-create)
        try:
            broker.ensure_topic(topic)
        except Exception:
            # Be tolerant: if a broker doesn't implement ensure_topic, continue
            pass

        # Publish the task message
        msg_id = broker.publish(topic=topic, payload=context.to_payload(), headers=headers or {"type": "task"})
        logging.debug(f"broker.publish msg_id : {msg_id} onto topic : {topic}")
        return context.task_id

    # @classmethod
    # def get_all_active_tasks(cls, topic: str = DEFAULT_TOPIC) -> list[Dict[str, Any]]:
    #     """
    #     Convenience method to fetch active tasks from the underlying broker.
    #     Returns a list of dicts with at least: id, topic, payload, headers, attempts, created_at, state.
    #     """
    #     broker = cls._get_broker()
    #     try:
    #         return broker.get_all_active_tasks(topic)
    #     except AttributeError:
    #         # Broker may not implement the optional API
    #         return []

    # @classmethod
    # def start_executor(cls):
    #     pass
    #     # start a task runner

    @classmethod
    def init_worker(cls, fast_pluggy):
        """
        Initialize workers.

        """

        from .config import TasksRunnerSettings

        settings: TasksRunnerSettings = TasksRunnerSettings()

        # Start the background executor (idempotent)
        if not fast_pluggy.has_global('tasks_worker.executor'):
            from .core.events import TaskEventBus
            from .core.runner import TaskRunner

            bus = TaskEventBus()
            runner = TaskRunner(fp=fast_pluggy, bus=bus)
            broker = TaskWorker._get_broker()
            executor = runner.start_executor(broker=broker, topics=['*'])

            # Expose references in global registry for reuse and possible shutdown
            fast_pluggy.register_global('tasks_worker.bus', bus)
            fast_pluggy.register_global('tasks_worker.runner', runner)
            fast_pluggy.register_global('tasks_worker.executor', executor)

        # Discover tasks
        if settings.enable_auto_task_discovery:
            from .registry.discovery import discover_tasks_from_loaded_modules
            discover_tasks_from_loaded_modules(fast_pluggy=fast_pluggy)

        if settings.discover_celery_tasks:
            from .celery_compat import init_celery_compat
            init_celery_compat(settings)

        # Launch scheduler in background
        if settings.scheduler_enabled:
            from .tasks.scheduler import schedule_loop
            TaskWorker.submit(
                schedule_loop,
                task_name="Scheduler",
                allow_concurrent=False,
                max_retries=-1
            )

    @staticmethod
    def setup_broker(topic_settings: dict | None = None):
        """
        Construct the configured broker and run its startup hook.
        Use this at application startup (e.g., before launching uvicorn) to ensure
        broker-specific prerequisites are ready. Returns the broker instance.

        New: You can pass per-topic settings, e.g.
            TaskWorker.setup_broker(topic_settings={
                'ia': {'global_concurrency': 1}
            })
        Supported keys per topic dict:
            - global_concurrency (int | None)
        Alternatively, the value for a topic can be an int/None directly.
        """
        from .broker.factory import get_broker
        broker = get_broker()
        # All brokers inherit a default no-op setup(); specific backends can override
        # to perform work (LocalBroker ensures BaseManager is running/connected).
        try:
            broker.setup()
        except Exception:
            # Be defensive: setup should not crash the app if a backend chooses no-op behavior
            pass

        # Apply per-topic global concurrency settings if provided
        if topic_settings:
            try:
                for topic, cfg in (topic_settings or {}).items():
                    limit = None
                    if isinstance(cfg, dict):
                        limit = cfg.get('global_concurrency')
                    else:
                        # accept direct int/None
                        limit = cfg
                    # Normalize and apply
                    try:
                        if limit is None or limit == 'none':
                            broker.set_topic_concurrency_limit(topic, None)
                        else:
                            broker.set_topic_concurrency_limit(topic, int(limit))
                    except Exception as e:
                        logging.warning(f"Failed to apply topic concurrency for '{topic}': {e}")
            except Exception as e:
                logging.exception(f"Error while applying topic_settings: {e}")
        return broker

    @staticmethod
    def set_task_progression(value: float, message: Optional[str] = None, meta: Optional[Dict[str, Any]] = None):
        """
        Update the current task's progress (0..100).
        Automatically resolves current task_id via ContextVar.
        """
        pass
        # todo emit event for progress
        #task_progress.update(value, message, meta)

    @staticmethod
    def add_scheduled_task(**kwargs):
        from .persistence.repository.scheduled import ensure_scheduled_task_exists
        with session_scope() as db_session:
            return ensure_scheduled_task_exists(db=db_session,**kwargs)

