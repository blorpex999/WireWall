from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.config.defaults import build_default_settings
from app.ui.controller import AppController


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
