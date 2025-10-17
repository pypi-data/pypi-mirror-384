from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...core.status import TaskStatus


@dataclass
class TaskReport:
    task_id: str
    function: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, str] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.CREATED
    result: Optional[Any] = None
    logs: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    tracebacks: Optional[List[str]] = None
    duration: Optional[float] = None
    attempts: Optional[int] = None
    success: Optional[bool] = None
    worker_id: Optional[str] = None
    thread_native_id: Optional[str] = None
    thread_ident: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # serialize Enum to value
        d["status"] = self.status.value if isinstance(self.status, TaskStatus) else self.status
        return d
