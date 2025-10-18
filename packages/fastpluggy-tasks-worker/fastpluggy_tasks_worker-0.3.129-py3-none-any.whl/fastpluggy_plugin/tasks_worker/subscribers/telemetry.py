# telemetry.py
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict

from ..core.events import TaskLifecycleEvent
from ..core.status import TaskStatus


@dataclass
class TaskTelemetry:
    # totals
    submitted_total: int = 0
    completed_total: int = 0
    running_total: int = 0

    # per-topic breakdown
    running_per_topic: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    submitted_per_topic: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    completed_per_topic: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # ---- handlers: names must match "on_<TaskStatus.name.lower()>" ----

    def on_created(self, e: TaskLifecycleEvent) -> None:
        # purely informational; often emitted before enqueue
        pass

    def on_queued(self, e: TaskLifecycleEvent) -> None:
        topic = getattr(e.context, "topic", "unknown")
        self.submitted_total += 1
        self.submitted_per_topic[topic] += 1

    def on_running(self, e: TaskLifecycleEvent) -> None:
        topic = getattr(e.context, "topic", "unknown")
        self.running_total += 1
        self.running_per_topic[topic] += 1

    # Final states — SUCCESS, FAILED, CANCELLED, MANUAL_CANCELLED, ERROR, TIMEOUT, DEAD, SKIPPED
    def on_final(self, e: TaskLifecycleEvent) -> None:
        topic = getattr(e.context, "topic", "unknown")
        # decrement running (if we ever saw it as running)
        if self.running_total > 0:
            self.running_total -= 1
        if self.running_per_topic.get(topic, 0) > 0:
            self.running_per_topic[topic] -= 1
            if self.running_per_topic[topic] == 0:
                self.running_per_topic.pop(topic, None)

        # completion counters (only if it's a real terminal outcome)
        if e.status in {
            TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED,
            TaskStatus.MANUAL_CANCELLED, TaskStatus.ERROR, TaskStatus.TIMEOUT,
            TaskStatus.DEAD, TaskStatus.SKIPPED
        }:
            self.completed_total += 1
            self.completed_per_topic[topic] += 1

    # Optional: logs/progress events (no counters, but you can mine metadata)
    def on_logs(self, e: TaskLifecycleEvent) -> None:
        pass

    def on_progress(self, e: TaskLifecycleEvent) -> None:
        pass

    # Public snapshot for heartbeat/manager/etc.
    def snapshot(self) -> dict:
        return {
            "running": self.running_total,
            "running_per_topic": dict(self.running_per_topic),
            "submitted_total": self.submitted_total,
            "submitted_per_topic": dict(self.submitted_per_topic),
            "completed_total": self.completed_total,
            "completed_per_topic": dict(self.completed_per_topic),
        }
