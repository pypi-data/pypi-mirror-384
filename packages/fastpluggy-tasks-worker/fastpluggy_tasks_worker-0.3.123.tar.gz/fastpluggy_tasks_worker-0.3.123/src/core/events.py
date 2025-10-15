# events.py
import asyncio
import inspect
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type


from .context import TaskContext
from .status import TaskStatus


# --------- Event envelope ---------

@dataclass
class TaskLifecycleEvent:
    status: TaskStatus
    task_id: str
    context: TaskContext
    broker_msg_id: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


# Listener & predicate signatures
TaskEventListener = Callable[[TaskLifecycleEvent], Any]
Predicate = Callable[[TaskLifecycleEvent], bool]


# --------- Internal subscription model ---------

@dataclass
class _Sub:
    fn: TaskEventListener
    priority: int = 0
    once: bool = False
    predicate: Optional[Predicate] = None


def _method_owner(cls, name: str):
    for base in cls.__mro__:
        if name in base.__dict__:
            return base
    return None


# --------- Event bus ---------

class TaskEventBus:
    """
    Lightweight, thread-safe, synchronous event bus for Task lifecycle.
    - Priority ordering (higher first)
    - Once-only listeners
    - Predicates to filter per-event at runtime
    - Async listener support (awaitables are run via asyncio.run)
    - Custom error handler hook
    - subscribe_class is idempotent and stores the created instance; use get_instance(cls) to retrieve it
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._listeners: Dict[TaskStatus, List[_Sub]] = {}
        self._error_handler: Callable[[Exception, TaskLifecycleEvent], None] = (
            lambda exc, e: __import__("traceback").print_exc()
        )
        self._instances: Dict[Type, Any] = {}

    # ---- configuration ----

    def on_error(self, handler: Callable[[Exception, TaskLifecycleEvent], None]) -> None:
        """Override the default error handler for listener exceptions."""
        with self._lock:
            self._error_handler = handler

    # ---- subscription API ----

    def subscribe(
        self,
        status: TaskStatus,
        listener: TaskEventListener,
        *,
        priority: int = 0,
        once: bool = False,
        predicate: Optional[Predicate] = None,
    ) -> None:
        """
        Register a listener for a specific status.
        - priority: higher runs first
        - once: auto-unsubscribes after first successful call
        - predicate: runs before calling; if False, listener is skipped
        """
        with self._lock:
            arr = self._listeners.setdefault(status, [])
            arr.append(_Sub(listener, priority=priority, once=once, predicate=predicate))
            arr.sort(key=lambda s: s.priority, reverse=True)

    def subscribe_many(
        self,
        statuses: List[TaskStatus],
        listener: TaskEventListener,
        **opts: Any,
    ) -> None:
        """
        # todo : maybe useless now whe have subscribe_class
        Convenience to subscribe the same listener to multiple statuses.
        """
        for st in statuses:
            self.subscribe(st, listener, **opts)

    def subscribe_class(
        self,
        cls: Type,
        *,
        prefix: str = "on_",
        priority: int = 0,
        factory: Optional[Callable[[], Any]] = None,
    ) -> Any:
        """
        Automatically subscribe all event handler methods defined directly on a class
        following a naming convention.

        Handlers must be named using the provided prefix (default: ``on_``), for example:
        ``on_created``, ``on_running``, ``on_success``. For final task states,
        a generic ``on_final`` can be defined and will be used as a fallback.

        This is **idempotent**: if the class was already subscribed, the existing
        instance is returned and no new handlers are registered.
        Parameters
        ----------
        cls : Type
            The class containing handler methods. It will be instantiated automatically.
        prefix : str, optional
            The naming convention prefix for handler methods (default: "on_").
        priority : int, optional
            Priority used when subscribing the handlers (default: 0).
        factory : Callable[[], Any], optional
            A callable used to create an instance of the class. If not provided,
            ``cls()`` is used.

        Example
        -------
        The singleton instance of `cls` used for subscriptions.
        >>> class MyPersistence(BasePersistence):
        ...     def on_created(self, e): print("Task created")
        ...     def on_final(self, e): print(f"Task finished with {e.status}")
        ...
        >>> bus.subscribe_class(MyPersistence)

        Notes
        -----
        - Only methods **defined directly on the class** are subscribed.
          This naturally skips inherited no-op implementations in abstract base classes.
        - Final states (SUCCESS, FAILED, etc.) will try to use ``on_final`` if no
          per-status handler exists.
        """
        with self._lock:
            # Idempotent: return the existing instance if already subscribed
            if cls in self._instances:
                return self._instances[cls]

            # Instantiate the object
            obj = factory() if factory else cls()

            # Final task states that trigger on_final as fallback
            finals = {
                TaskStatus.SUCCESS,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
                TaskStatus.MANUAL_CANCELLED,
                TaskStatus.ERROR,
                TaskStatus.TIMEOUT,
                TaskStatus.DEAD,
            }

            for status in TaskStatus:
                # e.g., on_created, on_running, on_success, etc.
                exact_name = f"{prefix}{status.name.lower()}"

                # Check if method is explicitly defined on THIS class (not inherited)
                fn = cls.__dict__.get(exact_name)

                # If no exact match and status is a final state, check for generic on_final
                if fn is None and status in finals:
                    fn = cls.__dict__.get(f"{prefix}final")

                # If we found a method, subscribe it using the bound instance method
                if fn is not None:
                    self.subscribe(status, getattr(obj, fn.__name__), priority=priority)

            # Store the instance for later retrieval
            self._instances[cls] = obj
            return obj

    def unsubscribe(self, status: TaskStatus, listener: TaskEventListener) -> None:
        """Remove a previously registered listener."""
        with self._lock:
            if status in self._listeners:
                self._listeners[status] = [s for s in self._listeners[status] if s.fn is not listener]
                if not self._listeners[status]:
                    self._listeners.pop(status, None)

    @contextmanager
    def subscribed(self, status: TaskStatus, listener: TaskEventListener, **opts: Any):
        """
        Context manager to temporarily subscribe a listener.
        Useful in tests or short-lived scopes.
        """
        self.subscribe(status, listener, **opts)
        try:
            yield
        finally:
            self.unsubscribe(status, listener)

    # ---- emission ----

    def emit(self, event: TaskLifecycleEvent) -> None:
        """
        Emit synchronously. If a listener returns an awaitable, it's executed
        with asyncio.run() (safe in worker threads).
        """
        # Snapshot under lock
        with self._lock:
            subs = list(self._listeners.get(event.status, []))

        to_remove: List[TaskEventListener] = []

        for sub in subs:
            # Predicate filter
            if sub.predicate and not self._safe_predicate(sub.predicate, event):
                continue

            try:
                res = sub.fn(event)
                if inspect.isawaitable(res):
                    asyncio.run(res)
            except Exception as exc:
                self._error_handler(exc, event)

            if sub.once:
                to_remove.append(sub.fn)

        # Clean up once-only listeners that actually ran
        if to_remove:
            with self._lock:
                if event.status in self._listeners:
                    self._listeners[event.status] = [s for s in self._listeners[event.status] if s.fn not in to_remove]
                    if not self._listeners[event.status]:
                        self._listeners.pop(event.status, None)

    # ---- ergonomics ----

    def emit_status(
        self,
        status: TaskStatus | str,
        *,
        ctx: TaskContext,
        broker_msg_id: Optional[str] = None,
        **meta: Any,
    ) -> None:
        """Helper to build and emit a TaskLifecycleEvent in one call."""
        self.emit(
            TaskLifecycleEvent(
                status=status.value if isinstance(status, TaskStatus) else status,
                task_id=ctx.task_id,
                context=ctx,
                broker_msg_id=broker_msg_id,
                meta=meta or {},
            )
        )

    # ---- instance registry (NEW) ----

    def get_instance(self, cls: Type, default: Any = None) -> Any:
        """Return the singleton instance that was registered for `cls`, or default if none."""
        with self._lock:
            return self._instances.get(cls, default)

    def has_instance(self, cls: Type) -> bool:
        """True if `cls` has already been subscribed and an instance is stored."""
        with self._lock:
            return cls in self._instances

    # ---- internals ----

    @staticmethod
    def _safe_predicate(pred: Predicate, event: TaskLifecycleEvent) -> bool:
        try:
            return bool(pred(event))
        except Exception:
            return False
