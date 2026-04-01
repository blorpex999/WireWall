from __future__ import annotations

from app.models.entities import AppSettings

APP_NAME = "WireWall"
DEFAULT_OLLAMA_MODEL = "qwen2.5:14b"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 210

PROFILE_PRESETS: dict[str, dict[str, int | str]] = {
    "Normal": {
        "scan_interval_seconds": 2,
        "alert_threshold": 50,
        "dedup_window_seconds": 60,
        "reconnect_penalty": 15,
        "metadata_penalty": 5,
    },
    "Strict": {
        "scan_interval_seconds": 1,
        "alert_threshold": 35,
        "dedup_window_seconds": 60,
        "reconnect_penalty": 20,
        "metadata_penalty": 10,
    },
    "Presentation": {
        "scan_interval_seconds": 3,
        "alert_threshold": 60,
        "dedup_window_seconds": 120,
        "reconnect_penalty": 15,
        "metadata_penalty": 5,
    },
}


def build_default_settings() -> AppSettings:
    return AppSettings(
        app_name=APP_NAME,
        mode="real",
        scan_interval_seconds=int(PROFILE_PRESETS["Normal"]["scan_interval_seconds"]),
        history_retention_days=30,
        log_level="INFO",
        ollama_base_url=DEFAULT_OLLAMA_URL,
        ollama_model=DEFAULT_OLLAMA_MODEL,
        ollama_timeout_seconds=DEFAULT_OLLAMA_TIMEOUT_SECONDS,
        security_profile="Normal",
        theme="dark",
        export_directory="",
        alert_threshold=int(PROFILE_PRESETS["Normal"]["alert_threshold"]),
        dedup_window_seconds=int(PROFILE_PRESETS["Normal"]["dedup_window_seconds"]),
        dashboard_refresh_ms=1500,
        autostart_enabled=False,
        desktop_notifications_enabled=True,
        recommendation_mode="balanced",
        author_name="Equipe Ydays",
        organization_name="Ynov Campus",
    )
