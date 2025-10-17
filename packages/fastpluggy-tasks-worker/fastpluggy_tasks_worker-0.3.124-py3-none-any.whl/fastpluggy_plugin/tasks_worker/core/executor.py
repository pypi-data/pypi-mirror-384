# executor.py
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Optional, Set, List, Dict

from fastpluggy.core.tools.threads_tools import set_os_thread_name

from ..broker.contracts import Broker, BrokerMessage  # adapt import paths

log = logging.getLogger("TaskExecutor")

# Thread-local cache to avoid renaming repeatedly
_tls = threading.local()


def _ensure_os_thread_name(name: str) -> None:
    # Only attempt once per thread (idempotent & cheap)
    if getattr(_tls, "os_name_set", None) != name:
        set_os_thread_name(name)  # best-effort; returns bool, we ignore here
        _tls.os_name_set = name


# ---- concurrency helpers ----
class ResizableSemaphore:
    """A semaphore whose capacity can be changed at runtime."""

    def __init__(self, capacity: int):
        if capacity < 0:
            raise ValueError("capacity must be >= 0")
        self._cap = capacity
        self._sem = threading.Semaphore(capacity)
        self._lock = threading.Lock()
        self._held_to_enforce_lowering = 0

    def set_capacity(self, new_cap: int):
        if new_cap < 0:
            new_cap = 0
        with self._lock:
            delta = new_cap - self._cap
            self._cap = new_cap
            if delta > 0:
                # grow: release delta permits
                for _ in range(delta):
                    self._sem.release()
                self._held_to_enforce_lowering = max(0, self._held_to_enforce_lowering - delta)
            elif delta < 0:
                # shrink: acquire -delta permits and hold them
                need = -delta
                for _ in range(need):
                    self._sem.acquire()
                self._held_to_enforce_lowering = need

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        return self._sem.acquire(blocking=blocking, timeout=timeout) if timeout is not None else self._sem.acquire(
            blocking=blocking)

    def release(self):
        self._sem.release()

    @property
    def capacity(self) -> int:
        return self._cap


class TaskExecutor:
    """
    Minimal executor:
      - 1 dispatcher thread per topic
      - small ThreadPoolExecutor
      - ack on True, nack(requeue=True) on False
    No DLQ, no janitor, no extras. Add later if/when needed.
    """

    def __init__(
            self,
            broker: Broker,
            topics: Iterable[str],
            handler: Callable[[BrokerMessage], bool],
            worker_id: str,
            *,
            max_workers: int = max(1, (os.cpu_count() or 2)),
            poll_interval: float = 0.05,
            name: Optional[str] = None,
    ) -> None:
        self.broker = broker
        self.topics = list(topics)
        # Track topics in a threadsafe set so we can add dynamically
        self._topics_lock = threading.Lock()
        self._topics: Set[str] = set(str(t) for t in topics if t)

        self.handler = handler
        self.max_workers = max_workers
        self.poll_interval = poll_interval
        self.worker_id = worker_id
        self.name = name or "executor"

        self._stop = threading.Event()
        self._pool: Optional[ThreadPoolExecutor] = None
        self._dispatchers: list[threading.Thread] = []
        # map topic -> dispatcher thread
        self._dispatcher_by_topic: dict[str, threading.Thread] = {}
        # per-topic concurrency: topic -> ResizableSemaphore | None (None = unlimited)
        self._topic_sems: Dict[str, Optional[ResizableSemaphore]] = {}

        self._sems_lock = threading.Lock()

    def start_executor(self) -> None:
        """
        Create dispatcher threads and start executor.
        One dispatcher thread per topic and one pool of thread workers.
        """
        self._pool = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="task")
        # Start dispatchers for initial topics
        for topic in self._topics_snapshot():
            # default unlimited; then start exactly one dispatcher
            self._ensure_topic_limit_initialized(topic)  # default unlimited
            self._start_dispatcher_for_topic(topic)
        log.info(f"TaskExecutor started topics={self._topics_snapshot()} workers={self.max_workers}")

    def stop(self, *, wait: bool = True) -> None:
        self._stop.set()
        for t in self._dispatchers:
            t.join(timeout=2.0)
        if self._pool:
            self._pool.shutdown(wait=wait, cancel_futures=True)
        log.info("TaskExecutor stopped")

    # ---- dynamic topics API ----

    def add_topic(self, topic: str) -> bool:
        """
        Add a topic at runtime. If it's new, start a dispatcher thread for it.
        Returns True if added, False if it already existed.
        """
        topic = str(topic)
        with self._topics_lock:
            if topic in self._topics:
                return False
            self._topics.add(topic)
        # if executor already running, spawn a dispatcher for this topic
        # init its limit and spawn a dispatcher if running
        self._ensure_topic_limit_initialized(topic)

        if self._pool is not None:
            self._start_dispatcher_for_topic(topic)
        log.info(f"[TaskExecutor] Added topic '{topic}'")
        return True

    def list_topics(self) -> List[str]:
        return self._topics_snapshot()

    def _topics_snapshot(self) -> List[str]:
        with self._topics_lock:
            return list(self._topics)

    def _start_dispatcher_for_topic(self, topic: str) -> None:
        # Avoid duplicate threads if called twice
        if topic in self._dispatcher_by_topic:
            return
        t = threading.Thread(
            target=self._dispatch_loop,
            args=(topic,),
            name=f"dispatch:{topic}",
            daemon=True,
        )
        t.start()
        self._dispatchers.append(t)
        self._dispatcher_by_topic[topic] = t

    # ---- per-topic concurrency API ----
    def _ensure_topic_limit_initialized(self, topic: str) -> None:
        # Default = unlimited (None)
        with self._sems_lock:
            if topic not in self._topic_sems:
                self._topic_sems[topic] = None

    def set_topic_limit(self, topic: str, limit: Optional[int]) -> None:
        """Set per-topic concurrency. None = unlimited; int >= 0 = max parallel for this topic."""
        if limit is not None and limit < 0:
            raise ValueError("limit must be None or >= 0")
        with self._sems_lock:
            sem = self._topic_sems.get(topic)
            if limit is None:
                self._topic_sems[topic] = None
                log.info("[TaskExecutor] topic '%s' limit set to unlimited", topic)
                return
            if sem is None or not isinstance(sem, ResizableSemaphore):
                self._topic_sems[topic] = ResizableSemaphore(limit)
            else:
                sem.set_capacity(limit)
        log.info("[TaskExecutor] topic '%s' limit set to %s", topic, limit)

    def get_topic_limit(self, topic: str) -> Optional[int]:
        with self._sems_lock:
            sem = self._topic_sems.get(topic)
        if sem is None:
            return None
        if isinstance(sem, ResizableSemaphore):
            return sem.capacity
        return None

    def set_topic_limits(self, limits: Dict[str, Optional[int]]) -> None:
        """Bulk update of per-topic limits. Keys missing are left untouched."""
        for t, lim in limits.items():
            self.set_topic_limit(t, lim)

    def get_limits_snapshot(self) -> Dict[str, Optional[int]]:
        """Return {topic: limit_or_None} for heartbeat/manager visibility."""
        out: Dict[str, Optional[int]] = {}
        with self._sems_lock:
            for t, sem in self._topic_sems.items():
                out[t] = None if sem is None else sem.capacity
        return out

    # ---- internals ----

    def _dispatch_loop(self, topic: str) -> None:
        # Set native name for the dispatcher thread once
        _ensure_os_thread_name(f"dispatch:{topic}")

        idle = 0
        while not self._stop.is_set():
            # Enforce per-topic concurrency BEFORE claiming:
            with self._sems_lock:
                sem = self._topic_sems.get(topic)
            acquired = False
            if isinstance(sem, ResizableSemaphore):
                # Block until a slot is available (your chosen behavior)
                sem.acquire()
                acquired = True

            try:
                try:
                    msg = self.broker.claim(topic, worker_id=self.worker_id)
                except Exception as e:
                    log.exception(f"[{topic}] claim failed: {e}")
                    time.sleep(0.25)
                    # release the slot if we acquired one and claim errored
                    if acquired:
                        try:
                            sem.release()
                        except Exception:
                            pass
                    continue

                if msg is None:
                    idle = min(idle + 1, 20)
                    time.sleep(self.poll_interval * idle)
                    # nothing to do → free the pre-acquired slot
                    if acquired:
                        try:
                            sem.release()
                        except Exception:
                            pass
                    continue

                # got a message → reset backoff
                idle = 0

                if not self._pool:
                    # Shouldn't happen; put it back
                    try:
                        self.broker.nack(msg.id, requeue=True)
                    except Exception:
                        pass
                    if acquired:
                        try:
                            sem.release()
                        except Exception:
                            pass
                    continue

                # Pass sem only if we actually acquired it (for release in _run_one)
                self._pool.submit(self._run_one, topic, msg, sem if acquired else None)

            except Exception as e:
                # Catch-all so the loop doesn't die
                log.exception(f"[{topic}] dispatch loop error: {e}")
                time.sleep(0.25)
                # best-effort: if we held a slot, release it
                if acquired and isinstance(sem, ResizableSemaphore):
                    try:
                        sem.release()
                    except Exception:
                        pass

    def _run_one(self, topic: str, msg: BrokerMessage, sem: Optional[ResizableSemaphore]) -> None:
        # Stable OS-level worker thread name: task:<worker_id_prefix>:<idx>
        py_name = threading.current_thread().name  # e.g., "task_3"
        idx = py_name.split("_")[-1] if "_" in py_name else py_name
        _ensure_os_thread_name(f"task:{self.worker_id[:8]}:{idx}")

        ok = False
        try:
            ok = bool(self.handler(msg))
        except Exception as e:
            log.exception(f"[{topic}] handler raised: {e}")
            ok = False
        finally:
            # Broker finalize
            try:
                if ok:
                    self.broker.ack(msg.id)
                else:
                    self.broker.nack(msg.id, requeue=True)
            except Exception as e:
                log.exception(f"[{topic}] ack/nack failed for {msg.id}: {e}")
            finally:
                # Release per-topic slot if one was held
                if isinstance(sem, ResizableSemaphore):
                    try:
                        sem.release()
                    except Exception:
                        pass
