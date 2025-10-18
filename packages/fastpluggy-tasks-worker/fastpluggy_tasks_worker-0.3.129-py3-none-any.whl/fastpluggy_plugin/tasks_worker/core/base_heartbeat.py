from __future__ import annotations

import atexit
import logging
import threading
from abc import ABC, abstractmethod
from typing import Callable, Optional

log = logging.getLogger("HeartbeatingWorker")

HEARTBEAT_INTERVAL = 3.0  # seconds


class HeartbeatingWorker(ABC):
    """
    Base class that emits periodic heartbeats.
    - Keeps a local running counter (inc_running/dec_running) for backward compat.
    - Can read "running" from an external supplier (e.g., TaskTelemetry) if provided.
    - Tracks a capacity value you can adjust dynamically.
    - Calls abstract send_heartbeat(running=..., capacity=...) on each tick.
    - Calls on_unregister() on stop (and optionally via atexit).
    """

    def __init__(
            self,
            *,
            worker_id: Optional[str] = None,
            heartbeat_interval: float = HEARTBEAT_INTERVAL,
            unregister_at_exit: bool = True,
            running_supplier: Optional[Callable[[], int]] = None,
    ) -> None:
        self.worker_id = worker_id or "worker"
        self.heartbeat_interval = float(heartbeat_interval)
        self.unregister_at_exit = bool(unregister_at_exit)

        # thread bits
        self._hb_thread: Optional[threading.Thread] = None
        self._hb_stop = threading.Event()

        # running counter (fallback)
        self._running_lock = threading.Lock()
        self._running_count = 0
        self._running_supplier = running_supplier

        # advertised capacity
        self._capacity = 0
        # forbid worker_id changes once started (helps broker accounting)
        self._frozen_id = False

        if self.unregister_at_exit:
            atexit.register(self._atexit_unregister)

    # ------------------------ public API ------------------------

    def start_heartbeat(self) -> None:
        if self._hb_thread and self._hb_thread.is_alive():
            return
        self._hb_stop.clear()
        self._hb_thread = threading.Thread(
            target=self._heartbeat_loop, name="hb:worker", daemon=True
        )
        self._hb_thread.start()
        # freeze the id to avoid accidental changes mid-flight
        self._frozen_id = True
        log.info("[Heartbeat] started for worker_id=%s interval=%.2fs", self.worker_id, self.heartbeat_interval)

    def stop_heartbeat(self) -> None:
        self._hb_stop.set()
        t = self._hb_thread
        if t and t.is_alive():
            t.join(timeout=self.heartbeat_interval * 2)
        self._hb_thread = None
        log.info(f"[Heartbeat] stopped for worker_id={self.worker_id}")

    def set_capacity(self, new_capacity: int) -> None:
        self._capacity = max(0, int(new_capacity))

    def get_capacity(self) -> int:
        return int(self._capacity)

    def set_running_supplier(self, fn: Optional[Callable[[], int]]) -> None:
        """Provide a callable returning the current running count (e.g., from TaskTelemetry)."""
        self._running_supplier = fn

    # --- legacy counter (kept for backward compatibility) ---

    def inc_running(self) -> None:
        with self._running_lock:
            self._running_count += 1

    def dec_running(self) -> None:
        with self._running_lock:
            self._running_count = max(0, self._running_count - 1)

    def get_running(self) -> int:
        # Prefer external provider (e.g., TaskTelemetry) if present
        if self._running_supplier is not None:
            try:
                return int(self._running_supplier())
            except Exception:
                # fall back to local counter if supplier misbehaves
                pass
        with self._running_lock:
            return self._running_count

    # ------------------------ internals ------------------------

    def _heartbeat_loop(self) -> None:
        backoff = self.heartbeat_interval
        while not self._hb_stop.is_set():
            try:
                running = self.get_running()
                capacity = self.get_capacity()
                self.send_heartbeat(running=running, capacity=capacity)
                # successful tick → reset backoff
                backoff = self.heartbeat_interval
            except Exception as e:
                log.debug("[Heartbeat] send_heartbeat error: %s", e, exc_info=False)
                # light jitter/backoff on error, but don't spam logs
                backoff = min(max(1.0, backoff * 1.25), self.heartbeat_interval * 3)
            finally:
                self._hb_stop.wait(backoff)

    def _atexit_unregister(self) -> None:
        try:
            self.stop_heartbeat()
        except Exception:
            pass
        try:
            self.on_unregister()
        except Exception:
            pass

    # ------------------------ to be implemented by subclass ------------------------

    @abstractmethod
    def send_heartbeat(self, *, running: int, capacity: int) -> None:
        """Called on each tick; publish heartbeat to your broker/registry."""
        raise NotImplementedError

    @abstractmethod
    def on_unregister(self) -> None:
        """Called once at shutdown (and at atexit if enabled)."""
        raise NotImplementedError

    # ------------------------ utility ------------------------

    def set_worker_id(self, worker_id: str) -> None:
        if self._frozen_id:
            log.warning(f'[Heartbeat] worker_id is frozen; ignoring change to {worker_id}')
            return
        self.worker_id = str(worker_id)
