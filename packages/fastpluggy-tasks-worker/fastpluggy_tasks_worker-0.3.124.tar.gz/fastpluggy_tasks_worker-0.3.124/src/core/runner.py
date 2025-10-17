# runner.py
import inspect
import logging
import os
import socket
import threading
import uuid
from typing import Any, Callable, Dict, Optional, Tuple, Type

from fastpluggy.core.tools.inspect_tools import call_with_injection
from fastpluggy.fastpluggy import FastPluggy

from .base_heartbeat import HeartbeatingWorker  # NEW: the base class
from .context import TaskContext
from .events import TaskEventBus
from .executor import TaskExecutor
from .executor_manager import ExecutorManager
from .log_handler import log_handler_context
from .status import TaskStatus
from .utils import it_allow_concurrent, path_to_func
from .. import set_current_task_ctx
from ..broker.contracts import BrokerMessage  # or your contracts.BrokerMessage
from ..subscribers import TaskTelemetry

log = logging.getLogger("TaskRunner")

# --- Exception policy (optional but recommended) --------------------------------
FATAL_EXC: Tuple[Type[BaseException], ...] = (
    ImportError, AttributeError, TypeError, ValueError,  # wrong func / signature / payload issues
)
RETRIABLE_EXC: Tuple[Type[BaseException], ...] = (
    TimeoutError, ConnectionError, OSError,  # infra/transient
)

MAX_ATTEMPTS = 5


def make_worker_id() -> str:
    # readable + unique; tweak as you like
    return f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"


class TaskRunner(HeartbeatingWorker):
    """
    Ultra-thin, broker-driven runner:
      - rebuilds TaskContext from payload
      - emits lifecycle via TaskEventBus
      - executes callable once (no in-task retries)
      - optional broker-side concurrency locks
      - heartbeats and unregister via HeartbeatingWorker base
    """

    def __init__(self, fp: FastPluggy, bus: TaskEventBus) -> None:
        self.worker_id = make_worker_id()
        super().__init__(worker_id=self.worker_id)
        self.fp = fp
        self.bus = bus

        # broker + executor references (set in start_executor)
        self._broker = None
        self._executor: Optional[TaskExecutor] = None

        # topics (purely informational for registration)
        self._topics: list[str] = []

        # local guard used when you want to read/update capacity at runtime
        self._capacity_lock = threading.Lock()

        # Explicitly declare manager so it's always available
        self._manager = None

    # -------------------------- public --------------------------

    def resolve_topics(self, broker, topics: Optional[list[str]]) -> list[str]:
        """
        Resolve the list of topics the executor should consume.
        - If topics is None/empty or contains '*', attempt to fetch all topics from the broker via get_topics().
          Each item may be an object with a 'topic' attribute or a dict with key 'topic'.
        - If fetching topics fails, returns [].
        - Otherwise, return the provided topics filtered to non-empty and coerced to str.
        This helper isolates logic for easier unit testing.
        """
        resolved: list[str] = []
        raw_topics = list(topics) if topics else []
        try:
            wants_all = (not raw_topics) or ("*" in raw_topics)
        except Exception:
            wants_all = True
        if wants_all:
            try:
                infos = broker.get_topics() or []
                for t in infos:
                    topic = getattr(t, 'topic', None) or (t.get('topic') if isinstance(t, dict) else None)
                    if topic:
                        resolved.append(str(topic))
            except Exception:
                # If broker cannot list topics, return empty to avoid spinning threads with no topic
                resolved = []
        else:
            resolved = [str(t) for t in raw_topics if t]
        return resolved

    def start_executor(
            self,
            broker,  # any Broker impl
            topics: Optional[list[str]] = None,
            *,
            max_workers: int = 8,
            poll_interval: float = 0.02,
    ) -> TaskExecutor:
        self._broker = broker
        self._broker.wait_ready()

        # Resolve topics via helper for cleanliness and testability
        resolved_topics = self.resolve_topics(broker=broker, topics=topics)

        self._topics = topics
        with self._capacity_lock:
            self.set_capacity(int(max_workers))

        from ..subscribers import setup_persistance
        setup_persistance(bus=self.bus)

        # Retrieve the singleton TaskTelemetry created by setup_persistance
        # and feed its "running" into the heartbeat BEFORE starting it.
        try:
            from ..subscribers.telemetry import TaskTelemetry
            telemetry = self.bus.get_instance(TaskTelemetry)
            if telemetry is not None:
                self.set_running_supplier(lambda: telemetry.snapshot()["running"])
        except Exception:
            pass

        # Register worker with broker (role if available) # todo maybe not useful now, and should be deleted
        role = getattr(broker, "role", None)
        self._broker.register_worker(
            worker_id=self.worker_id,
            pid=os.getpid(),
            host=socket.gethostname(),
            topics=self._topics,
            capacity=self._capacity,  # from base
            role=role,
            meta=None,
        )

        handler = self._build_handler()

        exe = TaskExecutor(
            broker=broker,
            topics=resolved_topics,
            handler=handler,  # must return True (ACK) / False (NACK)
            max_workers=max_workers,
            poll_interval=poll_interval,
            worker_id=self.worker_id,
        )
        exe.start_executor()
        self._executor = exe

        self._manager = ExecutorManager(
            broker=broker,
            executor=exe,
            topics=topics,
            interval=3.0,
        )
        self._manager.start()

        # Start heartbeat loop (from base)
        self.start_heartbeat()
        return exe

    def stop(self) -> None:
        """Stop heartbeat and unregister the worker (call at app shutdown)."""

        # Stop watcher first so it doesn't add while we shutdown
        if self._manager:
            self._manager.stop()

        self.stop_heartbeat()  # from base; will also be called by atexit as a safety net
        self.on_unregister()  # explicit, immediate unregister

    # -------------------------- HeartbeatingWorker hooks ------------------------

    def send_heartbeat(self, *, running: int, capacity: int) -> None:
        broker = self._broker
        if not broker:
            return

        # --- Task telemetry (event-driven via bus) ---
        telemetry_snapshot = {}
        try:
            telemetry = self.bus.get_instance(TaskTelemetry)
            if telemetry:
                telemetry_snapshot = telemetry.snapshot()
        except Exception:
            pass

        # --- Executor / pool stats (optional if you added get_pool_stats) ---
        exec_stats = {}
        try:
            if self._executor and hasattr(self._executor, "get_pool_stats"):
                exec_stats = self._executor.get_pool_stats() or {}
        except Exception:
            pass

        # --- Per-topic limits snapshot (worker-local, if implemented) ---
        limits = {}
        try:
            if self._executor and hasattr(self._executor, "get_limits_snapshot"):
                limits = self._executor.get_limits_snapshot() or {}
        except Exception:
            pass

        # --- Broker-wide limits & inflight (cluster view) ---
        global_limits, global_inflight = {}, {}
        try:
            if hasattr(broker, "get_topic_concurrency_limits"):
                global_limits = broker.get_topic_concurrency_limits() or {}
            if hasattr(broker, "get_topic_inflight"):
                global_inflight = broker.get_topic_inflight() or {}
        except Exception:
            pass

        # --- System info (optional; safe if psutil missing) ---
        system = {}
        try:
            import psutil
            import os
            cpu_pct = psutil.cpu_percent(interval=None)
            mem_pct = psutil.virtual_memory().percent
            try:
                load_avg = list(os.getloadavg())
            except Exception:
                load_avg = []
            system = {"cpu_pct": cpu_pct, "mem_pct": mem_pct, "load_avg": load_avg}
        except Exception:
            pass

        # --- Build meta payload and send ---
        meta = {
            "telemetry": telemetry_snapshot,  # task lifecycle (event-driven)
            "executor": exec_stats,  # thread-pool view (if provided)
            "limits": limits,  # worker-local per-topic limits
            "global_limits": global_limits,  # cluster-wide per-topic limits (broker-enforced)
            "global_inflight": global_inflight,  # cluster-wide inflight per topic
            "system": system,  # best-effort system snapshot
        }
        try:
            broker.heartbeat(self.worker_id, running=running, capacity=capacity, meta=meta)
        except Exception as e:
            # keep logs quiet; heartbeat errors shouldn't spam or crash
            log.debug("[TaskRunner] heartbeat failed: %s", e, exc_info=False)
    def on_unregister(self) -> None:
        try:
            if self._broker:
                self._broker.unregister_worker(self.worker_id)
        except Exception as e:
            log.debug(f"[TaskRunner] unregister error: {e}", exc_info=False)

    # -------------------------- internal --------------------------

    def _build_handler(self) -> Callable[[BrokerMessage], bool]:
        """
        Returns a function(msg) -> bool (True = ACK, False = NACK).
        Emits TaskStatus events so TaskTelemetry can track running/submitted/completed.
        """

        def _handler(msg: BrokerMessage) -> bool:
            func, ctx = self._resolve_func_and_context(msg)

            # Emit CREATED/RECEIVED (helps latency metrics)
            self.bus.emit_status(
                status=TaskStatus.CREATED,
                ctx=ctx,
                broker_msg_id=msg.id,
            )

            # Try to acquire broker-side lock if required
            lock_acquired = False
            lock_supported = False
            if ctx and (ctx.allow_concurrent is False):
                broker = getattr(self, "_broker", None)
                if broker and hasattr(broker, "acquire_lock"):
                    lock_supported = True
                    try:
                        lock_acquired = bool(broker.acquire_lock(
                            task_name=ctx.func_name,
                            task_id=ctx.task_id,
                            locked_by=self.worker_id,
                        ))
                        if not lock_acquired:
                            # Somebody else holds the lease → ACK skip
                            self.bus.emit_status(
                                TaskStatus.SKIPPED,
                                ctx=ctx,
                                broker_msg_id=msg.id,
                                reason="concurrency_lock",
                            )
                            return True
                    except Exception as err:
                        log.exception(f"[TaskRunner] acquire_lock error on {ctx.task_id}: {err}")
                        # Best-effort: proceed; alternatively NACK to retry

            # Mark RUNNING and increment running counter (for heartbeat)
            try:
                setattr(ctx, "worker_id", self.worker_id)
            except Exception:
                pass
            self.bus.emit_status(
                TaskStatus.QUEUED,
                ctx=ctx,
                broker_msg_id=msg.id,
            )
            self.inc_running()

            try:
                ok = self._run_once(func, ctx, msg)
            finally:
                # Decrement running no matter what
                self.dec_running()
                # Release lock if we acquired one
                if lock_supported and lock_acquired:
                    try:
                        self._broker.release_lock(task_id=ctx.task_id, locked_by=self.worker_id)
                    except Exception as err:
                        log.exception(f"[TaskRunner] release_lock error on {ctx.task_id}: {err}")

            # DLQ policy example using attempts (ACK on final failure)
            if not ok and getattr(msg, "attempts", 0) >= MAX_ATTEMPTS:
                self.bus.emit_status(
                    TaskStatus.FAILED,
                    ctx=ctx,
                    broker_msg_id=msg.id,
                    reason="max_attempts",
                )
                return True  # ACK so broker can DLQ server-side

            # Final status (SUCCESS → ACK True, FAILED → NACK False)
            self.bus.emit_status(
                TaskStatus.SUCCESS if ok else TaskStatus.FAILED,
                ctx=ctx,
                broker_msg_id=msg.id,
            )
            return ok

        return _handler

    def _resolve_func_and_context(self, msg: BrokerMessage) -> tuple[Callable[..., Any], TaskContext]:
        # Parse payload → context
        try:
            raw_ctx: Dict[str, Any] = msg.payload or {}
            ctx = TaskContext.from_payload(raw_ctx)
        except Exception as e:
            # Bad payload → return a stub func; final status will be emitted once in the main flow
            ctx_failed = TaskContext(task_id=msg.id, func_name="invalid", task_name="invalid", args=[], kwargs={},
                                     topic=getattr(msg, "topic", "unknown"))

            def _boom(*a, **k):
                raise ValueError(f"Bad payload for msg {msg.id}: {e}")

            # Attach a hint so you can enrich the final event if desired
            setattr(ctx_failed, "bad_payload_error", str(e))
            return _boom, ctx_failed

        # task_id
        if not ctx.task_id:
            ctx.task_id = msg.id or str(uuid.uuid4())

        # resolve callable
        try:
            func = path_to_func(ctx.func_name)
        except Exception as e:
            raise ImportError(f"Func not found: {ctx.func_name} ({e})")

        # backfill names if needed
        if not ctx.task_name:
            ctx.task_name = getattr(func, "__name__", "task")
        if not ctx.func_name:
            ctx.func_name = getattr(func, "__name__", "task")

        # infer allow_concurrent if None
        if ctx.allow_concurrent is None:
            ctx.allow_concurrent = it_allow_concurrent(func)

        return func, ctx

    def _run_once(self, func: Callable[..., Any], ctx: TaskContext, msg: Optional[BrokerMessage] = None) -> bool:
        ok = False
        with log_handler_context(ctx) as handler:
            setattr(ctx, "thread_handler", handler)
            try:
                context_dict = {FastPluggy: self.fp, TaskContext: ctx}

                # robust arg binding (works with wrappers/cfuncs better than co_varnames)
                sig = inspect.signature(func)
                if "self" in sig.parameters:
                    from ..celery_compat.dummy import DummyTask
                    ctx.kwargs["self"] = DummyTask()

                bound = sig.bind_partial(*getattr(ctx, "args", []) or [], **(getattr(ctx, "kwargs", {}) or {}))
                bound.apply_defaults()
                self.bus.emit_status(
                    TaskStatus.RUNNING,
                    ctx=ctx,
                    broker_msg_id=getattr(msg, "id", None),
                )
                # Ensure TaskContext is visible via ContextVar during execution
                with set_current_task_ctx(ctx):
                    call_with_injection(
                        func,
                        context_dict=context_dict,
                        user_kwargs=bound.arguments,
                    )
                ok = True

            except FATAL_EXC as e:
                log.error(f"[TaskRunner] FATAL {ctx.task_id}: {e}", exc_info=True)
                ok = True  # ACK to avoid poison retry loops

            except RETRIABLE_EXC as e:
                log.warning(f"[TaskRunner] RETRYABLE {ctx.task_id}: {e}", exc_info=True)
                ok = False  # NACK to retry

            except Exception as e:
                log.error(f"[TaskRunner] UNKNOWN {ctx.task_id}: {e}", exc_info=True)
                ok = False  # choose: retry by default
        return ok
