# broker/local.py
# LocalBroker using BaseManager (server started explicitly via setup())

import logging
import os
import threading
from datetime import datetime, timezone, timedelta, UTC
from multiprocessing import Process
from multiprocessing.managers import BaseManager
from threading import Condition
from typing import Any, Dict, Optional, Tuple

import atexit
import time

from .contracts import (
    Broker,
    BrokerMessage,
    TopicInfo,
    WorkerInfo,
    ClusterStats,
    ActiveTaskInfo,
    LockInfo,
    TopicState,
    TopicConfig,
)


# ---------------------------
# Shared queue state (served by the manager process)
# ---------------------------
class _State:
    """
    Backend-owned, process-local state exposed over a BaseManager proxy.
    All methods that mutate/read shared state acquire the condition lock (self._cv).
    """

    def __init__(self) -> None:
        # Workers and their currently running task ids
        self._workers: Dict[str, WorkerInfo] = {}            # worker_id -> info
        self._worker_tasks: Dict[str, set[str]] = {}         # worker_id -> {msg_id, ...}

        # Topics: runtime mutable state (queue, inflight counter, config, dead-letter)
        self._topics: Dict[str, TopicState] = {}             # topic -> TopicState

        # Global map of all in-flight messages (by msg id)
        self._inflight: Dict[str, BrokerMessage] = {}        # msg_id -> BrokerMessage

        # Locks (no TTL, no renew). task_id -> {task_name, locked_by, acquired_at}
        self._locks: Dict[str, Dict[str, Any]] = {}
        # Optional reverse index to enforce name-level uniqueness: task_name -> task_id
        self._locks_by_name: Dict[str, str] = {}

        # Concurrency + synchronization primitives
        self._cv = Condition()
        self._next_id = 1

        # Misc/observability helpers
        self._hb_ttl = 10.0  # worker heartbeats TTL (seconds)

    # ---- topic helpers ----
    def ensure_topic(self, topic: str) -> TopicState:
        """
        Create topic state if it does not exist and return it.
        Always acquires the condition lock; safe to call from any code path.
        """
        with self._cv:
            ts = self._topics.get(topic)
            if ts is None:
                ts = TopicState()  # default empty queue, inflight=0, default TopicConfig
                self._topics[topic] = ts
            return ts

    # ------------- observability -------------
    def stats(self) -> ClusterStats:
        """Basic stats snapshot; currently returns cluster stats."""
        return self.get_cluster_stats()

    # ------------- core message ops -------------
    def publish(self, topic: str, payload: Dict[str, Any], headers: Optional[Dict[str, Any]] = None) -> str:
        """
        Enqueue a new message on the given topic.
        """
        if headers is None:
            headers = {}
        with self._cv:
            msg_id = f"local:{self._next_id}"
            self._next_id += 1
            msg = BrokerMessage(
                id=msg_id,
                topic=topic,
                payload=payload,
                headers=headers,
                attempts=0,
                created_at=datetime.now(timezone.utc),
            )
            self.ensure_topic(topic).q.append(msg)
            self._cv.notify_all()
            return msg_id

    def _has_global_permit(self, topic: str) -> bool:
        """
        Check if the topic has available global concurrency permits.
        Must be called under self._cv.
        """
        ts = self._topics.get(topic)
        if ts is None:
            return True
        limit = ts.config.concurrency_limit
        if limit is None:
            return True
        return ts.inflight < int(limit)

    def _choose_wildcard_topic(self) -> Optional[str]:
        """
        Deterministically select the first topic (alphabetical) that has messages
        and available concurrency permits. Must be called under self._cv.
        """
        for name in sorted(self._topics.keys()):
            ts = self._topics[name]
            if ts.q and self._has_global_permit(name):
                return name
        return None

    def claim(self, topic: str, worker_id: str) -> Optional[BrokerMessage]:
        """
        Pop one message from the topic queue (or any if topic='*'), mark it inflight,
        and associate it with the worker.
        """
        with self._cv:
            if topic == "*":
                real_topic = self._choose_wildcard_topic()
                if real_topic is None:
                    return None
                ts = self._topics[real_topic]
            else:
                real_topic = topic
                ts = self.ensure_topic(real_topic)
                if not ts.q:
                    return None
                # Respect concurrency limit BEFORE handing out a message
                if not self._has_global_permit(real_topic):
                    return None

            msg = ts.q.popleft()

            # Record who is claiming this message
            try:
                msg.headers["worker_id"] = worker_id
                msg.headers["claimed_at"] = datetime.now(timezone.utc).isoformat()
            except Exception:
                # headers should always be a dict, but be defensive
                msg.headers = {"worker_id": worker_id, "claimed_at": datetime.now(timezone.utc).isoformat()}

            msg.attempts += 1
            self._inflight[msg.id] = msg
            self._worker_tasks.setdefault(worker_id, set()).add(msg.id)

            # Account per-topic inflight
            ts.inflight += 1

            return msg

    def ack(self, msg_id: str) -> None:
        """
        Acknowledge: remove from inflight; clear worker task; auto-release any lock held by the task.
        """
        with self._cv:
            msg = self._inflight.pop(msg_id, None)
            if msg is None:
                return

            # Drop from the worker's running set if tracked
            try:
                wid = (msg.headers or {}).get("worker_id")
            except Exception:
                wid = None
            if wid:
                self._worker_tasks.get(wid, set()).discard(msg_id)

            # Decrement per-topic in-flight
            ts = self._topics.get(msg.topic)
            if ts and ts.inflight > 0:
                ts.inflight -= 1

            # Auto-release lock by task_id if present (defensive cleanup)
            try:
                task_id = (msg.payload or {}).get("task_id") or msg_id
                if task_id in self._locks:
                    self._release_lock_no_owner_check(task_id)
            except Exception:
                pass

            self._cv.notify_all()

    def nack(self, msg_id: str, requeue: bool = True) -> None:
        """
        Negative ack: remove from inflight; optionally requeue to the front; auto-release any lock.
        """
        with self._cv:
            msg = self._inflight.pop(msg_id, None)
            if msg is None:
                return

            # Remove from worker's running set if tracked
            try:
                wid = (msg.headers or {}).get("worker_id")
            except Exception:
                wid = None
            if wid:
                self._worker_tasks.get(wid, set()).discard(msg_id)

            # Decrement per-topic in-flight
            ts = self._topics.get(msg.topic)
            if ts and ts.inflight > 0:
                ts.inflight -= 1

            # Auto-release lock on nack too
            try:
                task_id = (msg.payload or {}).get("task_id") or msg_id
                if task_id in self._locks:
                    self._release_lock_no_owner_check(task_id)
            except Exception:
                pass

            # Requeue to the front if requested
            if requeue:
                self.ensure_topic(msg.topic).q.appendleft(msg)
                self._cv.notify_all()
            else:
                # If dead-letter is enabled, push to topic's dead queue (optional behavior)
                ts = self.ensure_topic(msg.topic)
                if ts.config.dead_letter_enabled:
                    ts.dead.append(msg)
                self._cv.notify_all()

    # ------------- worker presence -------------
    def register_worker(
        self,
        worker_id: str,
        *,
        pid: int,
        host: str,
        topics: list[str],
        capacity: int,
        role: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register (or upsert) a worker's presence and declared capacity/topics.
        """
        with self._cv:
            self._workers[worker_id] = WorkerInfo(
                worker_id=worker_id,
                host=host,
                pid=pid,
                capacity=int(capacity or 1),
                running=0,                      # updated dynamically from claim/ack
                stale=False,                    # computed on read via get_workers()
                topics=list(topics or []),
                started_at=datetime.now(timezone.utc).isoformat(),
                last_seen=datetime.now(timezone.utc).isoformat(),
                role=role,
                meta=dict(meta or {}),
                tasks=None,
                running_hint=None,              # optional hint provided by worker, not authoritative
            )
            self._worker_tasks.setdefault(worker_id, set())
            self._cv.notify_all()

    def heartbeat(
        self,
        worker_id: str,
        running: Optional[int] = None,
        capacity: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update last_seen and optional running/capacity hints for a worker.
        """
        with self._cv:
            w = self._workers.get(worker_id)
            if not w:
                return  # or raise
            w.last_seen = datetime.now(timezone.utc).isoformat()
            if capacity is not None:
                w.capacity = int(capacity)
            if running is not None:
                w.running_hint = int(running)
            if meta is not None:
                try:
                    if not isinstance(w.meta, dict):
                        w.meta = {}
                except Exception:
                    w.meta = {}
                w.meta["hb"] = meta
            self._cv.notify_all()

    def unregister_worker(self, worker_id: str) -> None:
        """
        Remove a worker from the registry.
        """
        with self._cv:
            self._workers.pop(worker_id, None)
            self._worker_tasks.pop(worker_id, None)
            self._cv.notify_all()

    # ------------- listings -------------
    def get_workers(self, include_tasks: bool = False, stale_after: Optional[float] = None) -> list[WorkerInfo]:
        """
        Return a list of workers with computed `running` and `stale` flags.
        """
        with self._cv:
            now = datetime.now(UTC)
            out: list[WorkerInfo] = []
            ttl = stale_after if stale_after is not None else self._hb_ttl
            for w in self._workers.values():
                running = len(self._worker_tasks.get(w.worker_id, ()))
                stale = (now - datetime.fromisoformat(w.last_seen)) > timedelta(seconds=ttl)
                topics = sorted(list(w.topics))
                tasks_list = None
                if include_tasks:
                    tasks_list = sorted(list(self._worker_tasks.get(w.worker_id, ())))
                out.append(WorkerInfo(
                    worker_id=w.worker_id,
                    host=w.host,
                    pid=int(w.pid),
                    capacity=int(w.capacity),
                    running=running,
                    stale=stale,
                    topics=topics,
                    started_at=w.started_at,
                    role=w.role,
                    meta=w.meta,
                    tasks=tasks_list,
                    last_seen=w.last_seen,
                    running_hint=w.running_hint,
                ))
            return out

    def get_topics(self) -> list[TopicInfo]:
        """
        Return a sorted snapshot for all topics as TopicInfo.
        """
        with self._cv:
            out: list[TopicInfo] = []
            for name, ts in self._topics.items():
                subscribers = sum(
                    1 for w in self._workers.values() if (name in w.topics) or ("*" in w.topics)
                )
                out.append(ts.to_info(name, subscribers))
            return sorted(out, key=lambda x: x.topic)

    def get_cluster_stats(self) -> ClusterStats:
        """
        Aggregate cluster-level metrics across workers and topics.
        """
        with self._cv:
            total_capacity = sum(w.capacity for w in self._workers.values())
            total_running = sum(len(s) for s in self._worker_tasks.values())
            topics = self.get_topics()
            return ClusterStats(
                workers=len(self._workers),
                total_capacity=total_capacity,
                total_running=total_running,
                topics=topics,
                broker_type="local",
            )

    def get_all_active_tasks(self, topic: Optional[str]) -> list[ActiveTaskInfo]:
        """
        Return a combined view of queued and in-flight messages.
        If topic is provided, restrict to that topic; if topic is None, return for all topics.
        """
        items: list[ActiveTaskInfo] = []
        with self._cv:
            # Queued items
            if topic is None:
                topic_items = [(name, ts.q) for name, ts in self._topics.items()]
            else:
                q = self._topics.get(topic, TopicState()).q
                topic_items = [(topic, q)]
            for _, q in topic_items:
                for m in list(q):
                    items.append(ActiveTaskInfo(
                        id=m.id,
                        topic=m.topic,
                        payload=m.payload,
                        headers=dict(m.headers or {}),
                        attempts=m.attempts,
                        created_at=m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else m.created_at,
                        state="queued",
                    ))
            # In-flight items
            for m in self._inflight.values():
                if topic is not None and m.topic != topic:
                    continue
                items.append(ActiveTaskInfo(
                    id=m.id,
                    topic=m.topic,
                    payload=m.payload,
                    headers=dict(m.headers or {}),
                    attempts=m.attempts,
                    created_at=m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else m.created_at,
                    state="inflight",
                ))
        return items

    # ------------- locks (no TTLs) -------------
    def get_locks(self) -> list[LockInfo]:
        """Return a list of currently held locks (observability only)."""
        with self._cv:
            return [
                LockInfo(
                    task_id=tid,
                    task_name=info.get("task_name"),
                    locked_by=info.get("locked_by"),
                    acquired_at=info.get("acquired_at"),
                )
                for tid, info in self._locks.items()
            ]

    def force_release_lock(self, task_id: str) -> bool:
        """Force release a lock regardless of ownership."""
        with self._cv:
            return self._release_lock_no_owner_check(task_id)

    # Internal unlock without owner check (used by ack/nack/force)
    def _release_lock_no_owner_check(self, task_id: str) -> bool:
        info = self._locks.pop(task_id, None)
        if not info:
            return False
        tname = info.get("task_name")
        if tname and self._locks_by_name.get(tname) == task_id:
            self._locks_by_name.pop(tname, None)
        self._cv.notify_all()
        return True

    def acquire_lock(self, task_name: str, task_id: str, locked_by: str) -> bool:
        """
        Acquire an exclusive, best-effort lock for a logical task key on this broker node.

        Parameters
        - task_name: Logical lock key. For clarity, this should be the fully-qualified function path
                     (e.g. "pkg.module:func" or "pkg.module.func"). All tasks using the same key are
                     mutually exclusive at a time. If empty, it falls back to task_id.
        - task_id  : Unique execution/run identifier (one per message). Used to track the specific holder.
        - locked_by: Worker identifier (string) used for observability/ownership checks on release.

        Behavior
        - Name-level exclusivity: at most one task_id can hold a lock for the same task_name concurrently.
        - Idempotency by task_id and owner: re-acquiring the same (task_name, task_id) by the same worker is OK.
        - No TTL and no renewal: the lock lives until explicitly released or force-released.

        Returns
        - True if the caller now holds the lock (or already held it idempotently), False otherwise.
        """
        if not task_id:
            return False
        if not task_name:
            task_name = task_id

        with self._cv:
            xid = self._locks_by_name.get(task_name)
            if xid and xid != task_id:
                return False

            self._locks[task_id] = {
                "task_id": task_id,
                "task_name": task_name,
                "locked_by": locked_by,
                "acquired_at": datetime.now(timezone.utc).isoformat(),
            }
            self._locks_by_name[task_name] = task_id
            self._cv.notify_all()
            return True

    def release_lock(self, task_id: str, locked_by: Optional[str] = None) -> bool:
        """
        Release a previously acquired lock by its run-specific task_id.
        If locked_by is provided, release only if ownership matches.
        """
        if not task_id:
            return False
        with self._cv:
            info = self._locks.get(task_id)
            if not info:
                return False
            if locked_by is not None and info.get("locked_by") != locked_by:
                return False
            return self._release_lock_no_owner_check(task_id)

    # ------------- topic configuration admin -------------
    def set_topic_config(self, topic: str, config: TopicConfig) -> None:
        """
        Set full topic configuration atomically for a topic.
        """
        with self._cv:
            ts = self.ensure_topic(topic)
            # Validate/normalize
            if config.concurrency_limit is not None and int(config.concurrency_limit) < 0:
                raise ValueError("concurrency_limit must be >= 0 or None")
            ts.config = TopicConfig(
                concurrency_limit=None if config.concurrency_limit is None else int(config.concurrency_limit),
                max_retries=config.max_retries,
                dead_letter_enabled=bool(config.dead_letter_enabled),
                retention_seconds=config.retention_seconds,
            )
            self._cv.notify_all()

    def get_topic_config(self, topic: str) -> TopicConfig:
        """Return current TopicConfig for a topic (ensuring it exists)."""
        with self._cv:
            return self.ensure_topic(topic).config

    def get_all_topic_configs(self) -> Dict[str, TopicConfig]:
        """Return snapshot of all topic configs."""
        with self._cv:
            return {name: ts.config for name, ts in self._topics.items()}

    # ---- Back-compat helpers built on top of TopicConfig ----
    def set_topic_concurrency_limit(self, topic: str, limit: Optional[int]) -> None:
        """Legacy: set only the concurrency limit for a topic."""
        self.set_topic_config(topic, TopicConfig(concurrency_limit=None if limit is None else int(limit)))

    def get_topic_concurrency_limits(self) -> Dict[str, Optional[int]]:
        """Legacy: map topic -> concurrency_limit."""
        with self._cv:
            return {name: ts.config.concurrency_limit for name, ts in self._topics.items()}

    def get_topic_inflight(self) -> Dict[str, int]:
        """Real-time per-topic inflight counters."""
        with self._cv:
            return {name: ts.inflight for name, ts in self._topics.items()}


# Single shared state in the manager process
_shared_state = _State()

def _get_state() -> _State:
    return _shared_state


class _Mgr(BaseManager):
    """Thin BaseManager subclass that exposes _State methods over an IPC boundary."""
    pass


# Expose the methods that the proxy object will allow callers to invoke.
_Mgr.register(
    "get_state",
    callable=_get_state,
    exposed=[
        # core message ops
        "publish", "claim", "ack", "nack",
        # observability
        "stats", "get_all_active_tasks", "get_topics", "get_workers", "get_cluster_stats",
        # locks
        "get_locks", "force_release_lock", "acquire_lock", "release_lock",
        # worker presence
        "register_worker", "heartbeat", "unregister_worker",
        # topic maintenance / config
        "ensure_topic",
        "set_topic_config", "get_topic_config", "get_all_topic_configs",
        # back-compat + counters
        "set_topic_concurrency_limit", "get_topic_concurrency_limits", "get_topic_inflight",
    ],
)


# ---------------------------
# Public Broker (client-only; server spawned by setup())
# ---------------------------
class LocalBroker(Broker):
    """
    Thin client that connects to the BaseManager server.
    Handles lazy connect + one-time reconnect for transient errors.
    """
    # Connexion partagée par process
    _client_lock = threading.Lock()
    _shared_mgr: Optional[_Mgr] = None
    _shared_proxy = None

    # Process serveur unique (started only by setup() in the master)
    _server_lock = threading.Lock()
    _server_proc: Optional[Process] = None

    def __init__(
        self,
        address: Tuple[str, int] = ("127.0.0.1", 50050),
        authkey: bytes = b"fp-broker",
        retries: int = 60,
        delay: float = 0.5,
    ) -> None:
        self.address = address
        self.authkey = authkey
        self.retries = retries
        self.delay = delay
        self.log = logging.getLogger(f"LocalBroker[{os.getpid()}]")

    # ---------- Start server (call only in the master process) ----------
    def setup(self) -> None:
        """Start BaseManager server in background ONCE."""
        with LocalBroker._server_lock:
            if LocalBroker._server_proc and LocalBroker._server_proc.is_alive():
                return  # already started

            def _serve(address, authkey):
                m = _Mgr(address=address, authkey=authkey)
                m.get_server().serve_forever()

            p = Process(target=_serve, args=(self.address, self.authkey), name="fp-brokerd", daemon=True)
            p.start()
            LocalBroker._server_proc = p
            atexit.register(self._stop_server_if_owner)
            self.wait_ready()

    def _stop_server_if_owner(self):
        p = LocalBroker._server_proc
        if p and p.is_alive():
            p.terminate()
            p.join(timeout=2)

    def wait_ready(self) -> None:
        """
        Wait until the manager server responds to a quick RPC (stats()).
        """
        last = None
        for _ in range(self.retries):
            try:
                self._ensure_connected()
                LocalBroker._shared_proxy.stats()  # quick RPC to validate
                return
            except Exception as e:
                last = e
                time.sleep(self.delay)
                logging.debug(f"Broker server not ready yet: {last}... waiting {self.delay}s... ")
        raise RuntimeError(f"Broker server not ready at {self.address}: {last}")

    # ---------- Worker-side connection (lazy) ----------
    def _ensure_connected(self):
        """
        Ensure there is a live proxy connected to the shared state.
        """
        with LocalBroker._client_lock:
            if LocalBroker._shared_proxy is not None:
                return LocalBroker._shared_proxy
            m = _Mgr(address=self.address, authkey=self.authkey)
            last = None
            for _ in range(self.retries):
                try:
                    m.connect()
                    LocalBroker._shared_mgr = m
                    LocalBroker._shared_proxy = m.get_state()
                    return LocalBroker._shared_proxy
                except Exception as e:
                    last = e
                    time.sleep(self.delay)
            raise RuntimeError(f"Cannot connect to broker at {self.address}: {last}")

    @classmethod
    def close(cls) -> None:
        """Call on worker shutdown to free the connection."""
        with cls._client_lock:
            if cls._shared_proxy is not None:
                try:
                    cls._shared_proxy._close()
                except Exception:
                    pass
                cls._shared_proxy = None
            cls._shared_mgr = None

    # ---------- Methods (lazy connect + single reconnect) ----------
    def _reconnect_once(self):
        with LocalBroker._client_lock:
            if LocalBroker._shared_proxy is not None:
                try:
                    LocalBroker._shared_proxy._close()
                except Exception:
                    pass
                LocalBroker._shared_proxy = None
            LocalBroker._shared_mgr = None
        return self._ensure_connected()

    # -------- core ops --------
    def publish(self, topic: str, payload: Dict[str, Any], headers: Optional[Dict[str, Any]] = None) -> str:
        p = self._ensure_connected()
        try:
            return p.publish(topic, payload, headers)
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return self._reconnect_once().publish(topic, payload, headers)

    def ensure_topic(self, topic: str) -> None:
        p = self._ensure_connected()
        try:
            p.ensure_topic(topic)
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            self._reconnect_once().ensure_topic(topic)

    def claim(self, topic: str, worker_id: str):
        p = self._ensure_connected()
        try:
            return p.claim(topic, worker_id)
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return self._reconnect_once().claim(topic, worker_id)

    def ack(self, msg_id: str) -> None:
        p = self._ensure_connected()
        try:
            p.ack(msg_id)
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            self._reconnect_once().ack(msg_id)

    def nack(self, msg_id: str, requeue: bool = True) -> None:
        p = self._ensure_connected()
        try:
            p.nack(msg_id, requeue)
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            self._reconnect_once().nack(msg_id, requeue)

    # -------- observability --------
    def stats(self):
        p = self._ensure_connected()
        try:
            return p.stats()
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return self._reconnect_once().stats()

    def get_all_active_tasks(self, topic: Optional[str]):
        p = self._ensure_connected()
        try:
            return p.get_all_active_tasks(topic)
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return self._reconnect_once().get_all_active_tasks(topic)

    # -------- worker presence --------
    def register_worker(self, worker_id, pid, host, topics, capacity, role=None, meta=None):
        self._ensure_connected().register_worker(worker_id, pid=pid, host=host, topics=topics,
                                                 capacity=capacity, role=role, meta=meta)

    def heartbeat(self, worker_id, running=None, capacity=None, meta=None):
        self._ensure_connected().heartbeat(worker_id, running, capacity, meta)

    def unregister_worker(self, worker_id):
        self._ensure_connected().unregister_worker(worker_id)

    def get_workers(self, include_tasks=False, stale_after=None):
        return self._ensure_connected().get_workers(include_tasks, stale_after)

    def get_topics(self):
        return self._ensure_connected().get_topics()

    def get_cluster_stats(self):
        return self._ensure_connected().get_cluster_stats()

    # -------- locks (no TTLs, no renew) --------
    def get_locks(self) -> list["LockInfo"]:
        p = self._ensure_connected()
        try:
            return p.get_locks()
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return self._reconnect_once().get_locks()

    def force_release_lock(self, task_id: str) -> bool:
        p = self._ensure_connected()
        try:
            return bool(p.force_release_lock(task_id))
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return bool(self._reconnect_once().force_release_lock(task_id))

    def acquire_lock(self, task_name: str, task_id: str, locked_by: str) -> bool:
        """
        Acquire an exclusive lock using a logical key on the broker side.
        Use the fully-qualified function path for task_name when you want to enforce
        single-flight execution per function across this worker fleet.

        Args:
            task_name: Logical lock key (recommended: function import path).
            task_id: Unique run/execution id of the message holding the lock.
            locked_by: Worker id attempting to hold the lock.
        Returns:
            True if the lock was acquired (or already held by the same task_id), False otherwise.
        """
        p = self._ensure_connected()
        try:
            return bool(p.acquire_lock(task_name, task_id, locked_by))
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return bool(self._reconnect_once().acquire_lock(task_name, task_id, locked_by))

    def release_lock(self, task_id: str, locked_by: Optional[str] = None) -> bool:
        p = self._ensure_connected()
        try:
            return bool(p.release_lock(task_id, locked_by))
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return bool(self._reconnect_once().release_lock(task_id, locked_by))

    # -------- topic configuration (client pass-throughs) --------
    def set_topic_config(self, topic: str, config: TopicConfig) -> None:
        p = self._ensure_connected()
        try:
            p.set_topic_config(topic, config)
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            self._reconnect_once().set_topic_config(topic, config)

    def get_topic_config(self, topic: str) -> TopicConfig:
        p = self._ensure_connected()
        try:
            return p.get_topic_config(topic)
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return self._reconnect_once().get_topic_config(topic)

    def get_all_topic_configs(self) -> Dict[str, TopicConfig]:
        p = self._ensure_connected()
        try:
            return p.get_all_topic_configs()
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return self._reconnect_once().get_all_topic_configs()

    # ---- Back-compat wrappers ----
    def set_topic_concurrency_limit(self, topic: str, limit: Optional[int]) -> None:
        p = self._ensure_connected()
        try:
            p.set_topic_concurrency_limit(topic, limit)
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            self._reconnect_once().set_topic_concurrency_limit(topic, limit)

    def get_topic_concurrency_limits(self) -> Dict[str, Optional[int]]:
        p = self._ensure_connected()
        try:
            return p.get_topic_concurrency_limits()
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return self._reconnect_once().get_topic_concurrency_limits()

    def get_topic_inflight(self) -> Dict[str, int]:
        p = self._ensure_connected()
        try:
            return p.get_topic_inflight()
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            return self._reconnect_once().get_topic_inflight()
