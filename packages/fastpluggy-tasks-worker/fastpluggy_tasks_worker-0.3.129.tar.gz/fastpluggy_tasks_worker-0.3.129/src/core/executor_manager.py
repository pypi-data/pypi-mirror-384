import logging
import threading
from typing import Optional


class ExecutorManager:
    """
    Minimal control-plane:
      - If topics contains '*' or is empty, enable wildcard mode
      - Periodically polls broker.get_topics()
      - Auto-adds new topics to the executor
    """

    def __init__(self, *, broker, executor, topics, interval: float = 3.0):
        self.broker = broker
        self.executor = executor
        self.interval = float(interval)

        # Detect wildcard behavior internally
        try:
            raw_topics = list(topics) if topics else []
            self.wildcard_enabled = (not raw_topics) or ("*" in raw_topics)
        except Exception:
            self.wildcard_enabled = True

        self._stop = threading.Event()
        self._thr: Optional[threading.Thread] = None

    def start(self) -> None:
        if not self.wildcard_enabled:
            logging.info("[TaskManager] wildcard not enabled; watcher not started")
            return
        if self._thr and self._thr.is_alive():
            return
        self._stop.clear()
        self._thr = threading.Thread(target=self._loop, name="manager:topic-watcher", daemon=True)
        self._thr.start()
        logging.info("[TaskManager] topic watcher started")

    def stop(self) -> None:
        self._stop.set()
        if self._thr and self._thr.is_alive():
            self._thr.join(timeout=2.0)
        self._thr = None
        logging.info("[TaskManager] topic watcher stopped")

    # --- internals ---
    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                topics = self._safe_get_topics()
                if topics:
                    for t in topics:
                        self.executor.add_topic(t)
            except Exception as e:
                logging.debug(f"[TaskManager] watcher error: {e}", exc_info=False)
            self._stop.wait(self.interval)

    def _safe_get_topics(self) -> list[str]:
        try:
            infos = self.broker.get_topics() or []
            return [
                str(getattr(item, "topic", None) or (item.get("topic") if isinstance(item, dict) else ""))
                for item in infos
                if (getattr(item, "topic", None) or (isinstance(item, dict) and item.get("topic")))
            ]
        except Exception:
            return []
