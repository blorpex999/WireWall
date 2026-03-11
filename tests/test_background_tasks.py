from __future__ import annotations

import threading
import time

from app.services.background_tasks import BackgroundTaskService
from app.services.event_bus import EventBus


def test_background_task_service_executes_async_job_and_deduplicates() -> None:
    bus = EventBus()
    service = BackgroundTaskService(bus, max_workers=1)
    release = threading.Event()
    started_flag = threading.Event()

    def slow_job():
        started_flag.set()
        release.wait(timeout=2)
        return ["ok"]

    try:
        started = service.submit_unique(
            "health_refresh",
            slow_job,
            success_event="health_refresh_completed",
            error_event="background_task_error",
        )
        assert started is True
        assert started_flag.wait(timeout=1) is True

        duplicate = service.submit_unique(
            "health_refresh",
            lambda: ["duplicate"],
            success_event="health_refresh_completed",
            error_event="background_task_error",
        )
        assert duplicate is False

        release.set()
        deadline = time.time() + 2
        events = []
        while time.time() < deadline:
            events = bus.drain()
            if events:
                break
            time.sleep(0.05)

        assert events
        assert events[0]["type"] == "health_refresh_completed"
        assert events[0]["payload"]["result"] == ["ok"]
    finally:
        release.set()
        service.shutdown()
