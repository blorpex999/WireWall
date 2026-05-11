from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.config.defaults import build_default_settings
from app.models.entities import DeviceEvent, HealthStatus
from app.ui.controller import AppController
from app.utils.datetime import utc_now


def test_controller_save_settings_rejects_invalid_numeric_values() -> None:
    settings = build_default_settings()
    controller = AppController(SimpleNamespace(settings=settings))

    with pytest.raises(ValueError, match="Frequence de scan|Fr"):
        controller.save_settings(
            {
                "scan_interval_seconds": "0",
                "history_retention_days": "30",
                "log_level": "INFO",
                "ollama_base_url": "http://127.0.0.1:11434",
                "ollama_model": "qwen2.5:14b",
                "ollama_timeout_seconds": "10",
                "security_profile": "Normal",
                "export_directory": "",
            }
        )


def test_controller_save_settings_rejects_non_local_ollama_url() -> None:
    settings = build_default_settings()
    controller = AppController(SimpleNamespace(settings=settings))

    with pytest.raises(ValueError, match="URL Ollama invalide"):
        controller.save_settings(
            {
                "scan_interval_seconds": "5",
                "history_retention_days": "30",
                "log_level": "INFO",
                "ollama_base_url": "https://example.com:11434",
                "ollama_model": "qwen2.5:14b",
                "ollama_timeout_seconds": "60",
                "security_profile": "Normal",
                "export_directory": "C:\\WireWall\\exports",
            }
        )


def test_controller_real_precheck_maps_blocking_and_warning_states() -> None:
    settings = build_default_settings()
    controller = AppController(SimpleNamespace(settings=settings))
    controller.get_health_statuses = lambda: [
        HealthStatus("usb_backend", "ok", "Backend libusb1 charge.", utc_now()),
        HealthStatus("database", "error", "SQLite indisponible.", utc_now()),
        HealthStatus("logs", "ok", "Logs accessibles.", utc_now()),
        HealthStatus("exports", "warning", "Exports non accessibles.", utc_now()),
        HealthStatus("admin", "warning", "Session non elevee.", utc_now()),
        HealthStatus("usbstor", "warning", "Lecture seule.", utc_now()),
    ]
    controller.get_ollama_health_status = lambda: HealthStatus("ollama", "warning", "Ollama absent.", utc_now())

    rows = {row["key"]: row for row in controller.get_demo_precheck()}

    assert rows["database"]["status"] == "Bloquant"
    assert rows["exports"]["status"] == "A surveiller"
    assert rows["ollama"]["status"] == "A surveiller"
    assert rows["model"]["status"] == "A surveiller"
    assert rows["usb_backend"]["status"] == "OK"


def test_controller_real_precheck_marks_real_mode_and_model_ready() -> None:
    settings = build_default_settings()
    settings.mode = "real"
    settings.ollama_model = "qwen2.5:14b"
    controller = AppController(SimpleNamespace(settings=settings))
    controller.get_health_statuses = lambda: [
        HealthStatus("usb_backend", "ok", "Backend libusb1 charge.", utc_now()),
        HealthStatus("database", "ok", "SQLite operationnelle.", utc_now()),
        HealthStatus("logs", "ok", "Logs accessibles.", utc_now()),
        HealthStatus("exports", "ok", "Exports accessibles.", utc_now()),
        HealthStatus("admin", "ok", "Session admin.", utc_now()),
        HealthStatus("usbstor", "ok", "Lecture OK.", utc_now()),
    ]
    controller.get_ollama_health_status = lambda: HealthStatus(
        "ollama",
        "ok",
        "Ollama repond localement.",
        utc_now(),
    )

    rows = {row["key"]: row for row in controller.get_demo_precheck()}

    assert rows["mode"]["status"] == "OK"
    assert rows["model"]["status"] == "OK"
    assert rows["ollama"]["status"] == "OK"
    assert "localement" in rows["ollama"]["detail"].lower()
    assert "modele" in rows["model"]["action"].lower()


def test_controller_start_services_starts_real_services() -> None:
    settings = build_default_settings()
    settings.mode = "real"
    calls: list[str] = []
    controller = AppController(
        SimpleNamespace(
            settings=settings,
            ollama_runtime_service=SimpleNamespace(ensure_started=lambda: calls.append("ollama")),
            usb_monitor=SimpleNamespace(start=lambda: calls.append("monitor")),
        )
    )

    controller.start_services()

    assert calls == ["ollama", "monitor"]


def test_controller_request_health_refresh_passes_real_mode() -> None:
    settings = build_default_settings()
    settings.mode = "real"
    calls: list[bool] = []

    class FakeBackgroundTasks:
        def submit_unique(self, name, func, success_event, error_event):
            assert name == "health_refresh"
            assert success_event == "health_refresh_completed"
            assert error_event == "background_task_error"
            func()
            return True

    controller = AppController(
        SimpleNamespace(
            settings=settings,
            background_tasks=FakeBackgroundTasks(),
            health_service=SimpleNamespace(run_all=lambda demo_mode=False: calls.append(demo_mode)),
        )
    )

    assert controller.request_health_refresh() is True
    assert calls == [False]


def test_controller_lists_notification_events_by_period() -> None:
    settings = build_default_settings()
    settings.mode = "real"
    now = utc_now()

    class FakeEventRepo:
        def list_recent(self, limit=500, demo_mode=False):
            assert limit == 500
            assert demo_mode is False
            return [
                DeviceEvent(now, "connected", "dev-1", "Device connected", "LOW", demo_mode=False),
                DeviceEvent(now, "snapshot_updated", None, "Snapshot refreshed", "LOW", demo_mode=False),
                DeviceEvent(now, "scan_error", None, "Scan failed", "WARNING", demo_mode=False),
            ]

    controller = AppController(SimpleNamespace(settings=settings, event_repo=FakeEventRepo()))

    events = controller.list_notification_events("24h")

    assert [event.event_type for event in events] == ["connected", "scan_error"]


def test_controller_request_health_refresh_passes_demo_mode() -> None:
    settings = build_default_settings()
    settings.mode = "demo"
    calls: list[bool] = []

    class FakeBackgroundTasks:
        def submit_unique(self, name, func, success_event, error_event):
            func()
            return True

    controller = AppController(
        SimpleNamespace(
            settings=settings,
            background_tasks=FakeBackgroundTasks(),
            health_service=SimpleNamespace(run_all=lambda demo_mode=False: calls.append(demo_mode)),
        )
    )

    assert controller.demo_mode is True
    assert controller.request_health_refresh() is True
    assert calls == [True]


def test_controller_run_ai_analysis_sync_passes_real_mode() -> None:
    settings = build_default_settings()
    settings.mode = "real"
    captured: dict[str, object] = {}
    analysis = SimpleNamespace(success=True)

    controller = AppController(
        SimpleNamespace(
            settings=settings,
            brain_service=SimpleNamespace(refresh=lambda demo_mode, recommendation_mode: captured.update({"brain": demo_mode})),
            report_service=SimpleNamespace(build_ai_context=lambda demo_mode: {"mode": "real", "demo": demo_mode}),
            ollama_service=SimpleNamespace(
                analyze=lambda context, demo_mode=False: captured.update({"context": context, "demo": demo_mode}) or analysis
            ),
            ai_analysis_repo=SimpleNamespace(add=lambda result: captured.update({"saved": result})),
        )
    )

    result = controller._run_ai_analysis_sync()

    assert result is analysis
    assert captured["brain"] is False
    assert captured["demo"] is False
    assert captured["context"] == {"mode": "real", "demo": False}
    assert captured["saved"] is analysis
