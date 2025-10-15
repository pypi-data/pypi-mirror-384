from enum import Enum


class TaskStatus(str, Enum): # todo : rename to task event
    CREATED ="created"
    QUEUED = "queued"
    RUNNING = "running"

    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    MANUAL_CANCELLED = "manual_cancelled"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"
    DEAD = "dead"

    UNKNOWN = "unknown"

    LOGS = "logs"
    PROGRESS = "progress" # todo: replace the progress system

    @property
    def badge_class(self):
        return {
            TaskStatus.CREATED: 'bg-secondary',
            TaskStatus.QUEUED: 'bg-info',
            TaskStatus.RUNNING: 'bg-primary',
            TaskStatus.SUCCESS: 'bg-success',
            TaskStatus.FAILED: 'bg-danger',
            TaskStatus.CANCELLED: 'bg-warning',
            TaskStatus.MANUAL_CANCELLED: 'bg-warning',
            TaskStatus.TIMEOUT: 'bg-warning',
        }.get(self, 'bg-secondary')  # Default to 'bg-secondary' if not found
