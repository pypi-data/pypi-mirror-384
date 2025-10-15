# broker/contracts.py
# ----------------------
# Common Broker interface and shared data structures that all broker backends must implement.
# Goal: swap implementations (Local/BaseManager, Redis, Postgres, etc.) without changing app code.
#
# Design notes:
# - BrokerMessage: a single task/message flowing through the system.
# - TopicState (internal): runtime, mutable state held by a backend for each topic (queue, inflight counters, config).
# - TopicInfo (external): read-only snapshot for APIs/metrics/UI; derived from TopicState.
# - TopicConfig: knobs to configure topics (e.g., concurrency limits).
# - WorkerInfo / ClusterStats / ActiveTaskInfo: structured observability and listings.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional, Union
from collections import deque


# ----------------------
# Core message type
# ----------------------
@dataclass
class BrokerMessage:
    """
    Represents a single message/task in the queue.
    Returned by the broker when a worker claims a task.
    """
    id: str                         # Unique ID, often prefixed with backend (e.g., "local:1", "pg:123")
    topic: str                      # Queue/topic name
    payload: Dict[str, Any]         # Task data
    headers: Dict[str, Any] = field(default_factory=dict)  # Extra metadata (worker_id, claimed_at, etc.)
    attempts: int = 0               # How many times this message has been claimed
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ----------------------
# Topic configuration (inputs)
# ----------------------
@dataclass
class TopicConfig:
    """
    Configuration knobs for a topic (cluster-wide). Extend safely over time.
    None means "unset" or "unlimited" depending on the field.
    """
    concurrency_limit: Optional[int] = None  # None => unlimited concurrency
    # Future-ready fields (may be no-ops in some backends until implemented)
    max_retries: Optional[int] = None
    dead_letter_enabled: bool = True
    retention_seconds: Optional[int] = None


# ----------------------
# Internal topic state (mutable, backend-owned)
# ----------------------
@dataclass
class TopicState:
    """
    INTERNAL ONLY: runtime state a backend maintains for each topic.
    Backends should not expose this directly; convert to TopicInfo for external views.
    # todo: maybe add subscriber worker_id
    """
    q: Deque[BrokerMessage] = field(default_factory=deque)  # Live FIFO queue of messages
    inflight: int = 0                                       # Count of messages currently claimed
    config: TopicConfig = field(default_factory=TopicConfig) # Current config for this topic
    dead: Deque[BrokerMessage] = field(default_factory=deque)  # Optional: dead-letter queue (if used)

    def to_info(self, name: str, subscribers: int) -> "TopicInfo":
        """
        Convert this internal state into a read-only TopicInfo snapshot for APIs/metrics.
        """
        return TopicInfo(
            topic=name,
            queued=len(self.q),
            inflight=self.inflight,
            dead_letter=len(self.dead),
            subscribers=subscribers,
            configuration=self.config,
        )


# ----------------------
# Topic snapshot (outputs)
# ----------------------
@dataclass
class TopicInfo:
    """
    EXTERNAL VIEW: read-only snapshot of a topic for dashboards and APIs.
    """
    topic: str
    queued: int
    inflight: int
    dead_letter: int
    subscribers: int
    configuration: TopicConfig = field(default_factory=TopicConfig)  # Strongly-typed config


# ----------------------
# Worker + cluster observability
# ----------------------
@dataclass
class WorkerInfo:
    """
    A worker process registered with the broker.
    """
    worker_id: str
    host: str
    pid: int
    capacity: int
    running: int
    running_hint: Optional[int]   # Optional hint reported by worker (authoritative linkage is claim/ack)
    stale: bool
    topics: List[str]
    started_at: str
    last_seen: str
    role: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    tasks: Optional[List[str]] = None  # Present only when include_tasks=True


@dataclass
class ClusterStats:
    """
    Aggregate cluster-level stats.
    """
    workers: int
    total_capacity: int
    total_running: int
    topics: List[TopicInfo] = field(default_factory=list)
    broker_type: Optional[str] = None


@dataclass
class ActiveTaskInfo:
    """
    A unified list item for active tasks (either queued or in-flight), for admin UIs.
    """
    id: str
    topic: str
    payload: Dict[str, Any]
    headers: Dict[str, Any]
    attempts: int
    created_at: Any
    state: str  # "queued" | "inflight"


@dataclass
class LockInfo:
    """
    Observability view of an exclusive lock acquired by a task run.
    """
    task_id: str
    task_name: Optional[str]
    locked_by: Optional[str]
    acquired_at: Optional[str]


# ----------------------
# Broker interface
# ----------------------
class Broker(ABC):
    """
    Abstract Broker base class.
    All broker backends must implement these synchronous methods.
    This allows the TaskRunner or FastAPI app to use a common interface without asyncio.

    Under the hood, Broker delegates to a backend:
        LocalBroker   : BaseManager + in-proc/shared state
        RedisBackend  : Redis Streams + consumer groups (future)
        PostgresBackend: FOR UPDATE SKIP LOCKED (future)
    """

    # Startup hook
    def setup(self) -> None:
        """
        Optional: perform broker-specific initialization at application startup.
        Example (LocalBroker): ensure the BaseManager server is started and accepting connections
        before launching the web server (e.g., uvicorn).
        Default: no-op.
        """
        return None

    # -------- Core message operations --------
    @abstractmethod
    def publish(self, topic: str, payload: Dict[str, Any], headers: Optional[Dict[str, Any]] = None) -> str:
        """
        Publish a new message to the given topic.
        Returns a broker-specific message ID.
        """
        ...

    @abstractmethod
    def claim(self, topic: str, worker_id: str) -> Optional[BrokerMessage]:
        """
        Claim one message from the given topic for a specific worker.
        Returns a BrokerMessage or None if no messages are available.
        """
        ...

    @abstractmethod
    def ack(self, msg_id: str) -> None:
        """
        Acknowledge successful processing of a message:
        remove it from the queue/in-flight tracking.
        """
        ...

    @abstractmethod
    def nack(self, msg_id: str, requeue: bool = True) -> None:
        """
        Negative acknowledgement: mark a message as failed.
        If requeue=True, the message is returned to the queue for retry.
        If requeue=False, it may be moved to a dead-letter state (backend-dependent).
        """
        ...

    # -------- Optional/extended API (default no-ops) --------
    def ensure_topic(self, topic: str) -> None:
        """Optional: ensure a topic/queue exists. Default: no-op; publish may auto-create."""
        return None

    def stats(self) -> Dict[str, Any]:
        """Optional: return a summary of broker status. Default: empty dict."""
        return {}

    def get_all_active_tasks(self, topic: Optional[str]) -> List[ActiveTaskInfo]:
        """
        Optional: return a list of active tasks known by the broker.
        If topic is None, return for all topics; otherwise restrict to the given topic.
        Active tasks may include queued and in-flight messages depending on implementation.
        """
        return []

    def register_worker(
        self,
        worker_id: str,
        *,
        pid: int,
        host: str,
        topics: List[str],
        capacity: int,
        role: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Optional: register a worker presence with the broker."""
        return None

    def heartbeat(
        self,
        worker_id: str,
        running: Optional[int] = None,
        capacity: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Optional: update worker heartbeat/capacity and attach extra observability metadata."""
        return None

    def unregister_worker(self, worker_id: str) -> None:
        """Optional: unregister a worker."""
        return None

    def get_workers(self, include_tasks: bool = False, stale_after: Optional[float] = None) -> List[Union[WorkerInfo, Dict[str, Any]]]:
        """Optional: list workers known to the broker. Prefer List[WorkerInfo] for structured schema."""
        return []

    def get_topics(self) -> List[Union[TopicInfo, Dict[str, Any]]]:
        """Optional: list topics with queue metrics. Prefer List[TopicInfo]."""
        return []

    def get_cluster_stats(self) -> Union[ClusterStats, Dict[str, Any]]:
        """Optional: aggregate cluster-level stats. Prefer ClusterStats."""
        return {}

    def get_locks(self) -> List[LockInfo]:
        """Optional: list current task locks (for exclusive tasks)."""
        return []

    def force_release_lock(self, task_id: str) -> bool:
        """Optional: force release a task lock if supported."""
        return False

    # -------- Topic configuration API --------
    def set_topic_config(self, topic: str, config: TopicConfig) -> None:
        """
        Set full topic configuration atomically.
        Backends MUST persist/propagate this so new claims respect the config.
        """
        raise NotImplementedError

    def get_topic_config(self, topic: str) -> TopicConfig:
        """Return the current TopicConfig for a topic (or default if missing)."""
        raise NotImplementedError

    def get_all_topic_configs(self) -> Dict[str, TopicConfig]:
        """Return a snapshot of all topic configs by topic name."""
        raise NotImplementedError

    # ---- Back-compat shim around TopicConfig.concurrency_limit ----
    def set_topic_concurrency_limit(self, topic: str, limit: Optional[int]) -> None:
        """
        Legacy convenience: set only the concurrency limit for a topic.
        Implemented via get/set_topic_config.
        """
        cfg = self.get_topic_config(topic)
        cfg.concurrency_limit = None if limit is None else int(limit)
        self.set_topic_config(topic, cfg)

    def get_topic_concurrency_limits(self) -> Dict[str, Optional[int]]:
        """Legacy convenience: map of topic -> concurrency_limit."""
        return {t: cfg.concurrency_limit for t, cfg in self.get_all_topic_configs().items()}

    # -------- Real-time counters --------
    def get_topic_inflight(self) -> Dict[str, int]:
        """
        Return current in-flight counts per topic (cluster-wide).
        Backends that can't provide this in real-time should raise NotImplementedError.
        """
        raise NotImplementedError
