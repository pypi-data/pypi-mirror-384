# tasks/context.py
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class TaskContext:
    """
    Canonical representation of a task before and during execution.
    This is what TaskWorker builds and what the executor consumes.
    """
    task_id: str
    task_name: str
    func_name: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    notifier_config: List[Dict[str, Any]] = field(default_factory=list)
    parent_task_id: Optional[str] = None
    max_retries: int = 0
    retry_delay: int = 0
    task_origin: str = "unk"  # e.g., "api", "cron", "manual"
    topic: str = None
    allow_concurrent: bool = True
    extra_context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    #started_at: datetime = field(default_factory=datetime.utcnow)

    # Runtime field - populated later by executor
    notifiers: Optional[Any] = None

    def to_payload(self) -> Dict[str, Any]:
        """
        Flatten this TaskContext for sending to the broker.
        """
        d = asdict(self)
        # Don't send runtime-only fields
        d.pop("notifiers", None)
        return d

    @classmethod
    def from_payload(cls, data: Dict[str, Any]) -> "TaskContext":
        """
        Reconstruct a TaskContext received from broker.
        """
        return cls(**data)

    def log_context(self, key: Any = None, value: Any = None, **kwargs):
        # Case 1: called like log_context({"foo": "bar"})
        if isinstance(key, dict):
            for k, v in key.items():
                self.extra_context[k] = v
                #dispatch_context(self.task_id, k, v)
            return

        # Case 2: called like log_context("key", "value")
        if key is not None and value is not None:
            self.extra_context[key] = value
            #dispatch_context(self.task_id, key, value)

        # Case 3: called like log_context(foo="bar", count=1)
        for k, v in kwargs.items():
            self.extra_context[k] = v
            #dispatch_context(self.task_id, k, v)