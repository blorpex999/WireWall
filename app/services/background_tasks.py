from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable


LOGGER = logging.getLogger(__name__)


class BackgroundTaskService:
    def __init__(self, event_bus, max_workers: int = 4) -> None:
        self.event_bus = event_bus
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="wirewall-bg")
        self._running: set[str] = set()
        self._lock = threading.Lock()

    def submit_unique(
        self,
        name: str,
        func: Callable[..., Any],
        *args: Any,
        success_event: str,
        error_event: str,
    ) -> bool:
        with self._lock:
            if name in self._running:
                return False
            self._running.add(name)

        future = self.executor.submit(func, *args)
        future.add_done_callback(
            lambda completed: self._handle_completion(name, completed, success_event=success_event, error_event=error_event)
        )
        return True

    def is_running(self, name: str) -> bool:
        with self._lock:
            return name in self._running

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)

    def _handle_completion(self, name: str, future: Future, *, success_event: str, error_event: str) -> None:
        with self._lock:
            self._running.discard(name)
        try:
            result = future.result()
        except Exception as exc:  # pragma: no cover - asynchronous safety net
            LOGGER.exception("Tâche de fond en échec: %s", name)
            self.event_bus.publish(error_event, {"task": name, "message": str(exc)})
            return
        self.event_bus.publish(success_event, {"task": name, "result": result})
