from __future__ import annotations

import queue
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue()

    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        self._queue.put({"type": event_type, "payload": payload or {}})

    def drain(self, limit: int = 50) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        while len(items) < limit:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return items
