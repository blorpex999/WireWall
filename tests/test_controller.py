from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.config.defaults import build_default_settings
from app.models.entities import HealthStatus
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
                "ollama_model": "qwen2.5:3b",
                "ollama_timeout_seconds": "10",
                "security_profile": "Normal",
                "export_directory": "",
            }
        )


def test_controller_demo_precheck_maps_blocking_and_warning_states() -> None:
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

    assert rows["database"]["status"] == "Bloquant demo"
    assert rows["exports"]["status"] == "A surveiller"
    assert rows["ollama"]["status"] == "A surveiller"
    assert rows["model"]["status"] == "A surveiller"
    assert rows["usb_backend"]["status"] == "OK"


def test_controller_demo_precheck_marks_demo_mode_and_model_ready() -> None:
    settings = build_default_settings()
    settings.mode = "demo"
    settings.ollama_model = "qwen2.5:3b"
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
        "Ollama repond localement avec le modele 'qwen2.5:3b'.",
        utc_now(),
    )

    rows = {row["key"]: row for row in controller.get_demo_precheck()}

    assert rows["mode"]["status"] == "A surveiller"
    assert rows["model"]["status"] == "OK"
    assert rows["ollama"]["status"] == "OK"
