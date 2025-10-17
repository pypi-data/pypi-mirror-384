# log_handler.py
from __future__ import annotations

import contextvars
import logging
import threading
from contextlib import contextmanager
from logging import LogRecord
from typing import Generator, List, Optional

try:
    # Optional: only needed if you want to bridge Loguru to stdlib logging
    from loguru import logger as loguru_logger
    _HAS_LOGURU = True
except Exception:  # pragma: no cover
    _HAS_LOGURU = False
    loguru_logger = None  # type: ignore


# --- Public exports ----------------------------------------------------------

__all__ = [
    "ThreadLocalHandler",
    "log_handler_context",
    "InjectTaskIdFilter",
    "submit_with_context",
]


# --- Context propagation (preferred over threading.local) --------------------

current_task_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_task_id", default=None
)
current_task_ctx: contextvars.ContextVar[Optional[object]] = contextvars.ContextVar(
    "current_task_ctx", default=None
)

# Back-compat: if other parts still rely on threading.local, keep it here.
thread_local_context = threading.local()


# --- Filters / Formatters ----------------------------------------------------

class InjectTaskIdFilter(logging.Filter):
    """
    Ensures every LogRecord has a `task_id` attribute.
    Pulls from ContextVar; if absent, leaves None.
    """
    def filter(self, record: LogRecord) -> bool:
        if not hasattr(record, "task_id"):
            record.task_id = current_task_id.get()
        if not hasattr(record, "context"):
            record.context = current_task_ctx.get()
        return True


class SafeFormatter(logging.Formatter):
    """
    A formatter that won't crash if a record is missing custom attrs.
    """
    def format(self, record: LogRecord) -> str:  # type: ignore[override]
        if not hasattr(record, "task_id"):
            record.task_id = None
        if not hasattr(record, "context"):
            record.context = None
        return super().format(record)


# --- Loguru bridge (optional) ------------------------------------------------

class LoguruToLoggingHandler:
    """
    Bridge for redirecting loguru logs to the standard logging system.
    """
    def __init__(self, level: int = logging.DEBUG):
        self.level = level

    def write(self, message: str) -> None:
        msg = message.strip()
        if msg:
            logging.getLogger("loguru").log(self.level, msg)

    def flush(self) -> None:  # pragma: no cover
        pass


# --- The capture handler -----------------------------------------------------

class ThreadLocalHandler(logging.Handler):
    """
    Captures ONLY records that match `target_task_id`.
    One handler per task context; no global stream.
    Thread-safe internal list.
    """

    def __init__(self, target_task_id: str, level: int = logging.NOTSET):
        super().__init__(level=level)
        self.target_task_id = target_task_id
        self._stream: List[str] = []
        self._lock = threading.Lock()

    def emit(self, record: LogRecord) -> None:  # type: ignore[override]
        try:
            # Discover the record's task_id
            task_id = getattr(record, "task_id", None)
            if task_id is None:
                task_id = current_task_id.get()

            # Drop anything that isn't for this task
            if task_id != self.target_task_id:
                return

            msg = self.format(record)
            with self._lock:
                self._stream.append(msg)

        except Exception:
            self.handleError(record)

    # Public API to inspect collected logs
    def get_stream_value(self, join: bool = True) -> List[str] | str:
        with self._lock:
            if join:
                return "\n".join(self._stream)
            return list(self._stream)

    # Optionally allow resetting/clearing between phases
    def clear(self) -> None:
        with self._lock:
            self._stream.clear()


# --- Context manager to install/uninstall handler ----------------------------

_filter_installed = False
_filter_lock = threading.Lock()


def _ensure_root_filter_installed() -> None:
    global _filter_installed
    if _filter_installed:
        return
    with _filter_lock:
        if _filter_installed:
            return
        root = logging.getLogger()
        # Avoid duplicate filter installs if user calls multiple times
        for f in getattr(root, "filters", []):
            if isinstance(f, InjectTaskIdFilter):
                _filter_installed = True
                return
        root.addFilter(InjectTaskIdFilter())
        _filter_installed = True


@contextmanager
def log_handler_context(context: object) -> Generator[ThreadLocalHandler, None, None]:
    """
    Install a handler that captures ONLY logs for `context.task_id`.
    Also tags records via ContextVars so libs that don't pass 'extra' still match.

    Usage:
        with log_handler_context(ctx) as handler:
            ... run task ...
        logs = handler.get_stream_value(join=True)
    """
    # The context must expose .task_id
    task_id = getattr(context, "task_id", None)
    if not task_id:
        raise ValueError("context must have a non-empty `task_id` attribute")

    # Set ContextVars for this scope (current thread / asyncio task)
    token_id = current_task_id.set(task_id)
    token_ctx = current_task_ctx.set(context)

    # Back-compat for code that still reads threading.local
    thread_local_context.task_id = task_id
    thread_local_context.context = context

    _ensure_root_filter_installed()

    root_logger = logging.getLogger()
    # Let handlers inherit unless the app wants to change it; DEBUG eases dev
    if root_logger.level == logging.NOTSET:
        root_logger.setLevel(logging.DEBUG)

    handler = ThreadLocalHandler(target_task_id=task_id)
    handler.setFormatter(SafeFormatter(
        fmt="[%(asctime)s] %(levelname)s [task=%(task_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root_logger.addHandler(handler)

    # Bridge loguru → std logging (track sink id so we remove just ours)
    sink_id = None
    if _HAS_LOGURU:
        sink_id = loguru_logger.add(LoguruToLoggingHandler(), level="DEBUG")

    try:
        yield handler
    finally:
        try:
            root_logger.removeHandler(handler)
        finally:
            # Remove only the sink we added
            if _HAS_LOGURU and sink_id is not None:
                try:
                    loguru_logger.remove(sink_id)
                except Exception:
                    pass

            # Reset ContextVars
            try:
                current_task_id.reset(token_id)
                current_task_ctx.reset(token_ctx)
            except Exception:
                # If already reset (rare), ignore
                pass

            # Clean threading.local
            for attr in ("task_id", "context"):
                if hasattr(thread_local_context, attr):
                    try:
                        delattr(thread_local_context, attr)
                    except Exception:
                        pass


