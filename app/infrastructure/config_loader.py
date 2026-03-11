from __future__ import annotations

import json
from pathlib import Path

from app.config.defaults import PROFILE_PRESETS, build_default_settings
from app.models.entities import AppSettings


class ConfigLoader:
    def __init__(self, config_file: Path) -> None:
        self.config_file = config_file

    def load(self) -> AppSettings:
        settings = build_default_settings()
        if not self.config_file.exists():
            return settings

        try:
            content = json.loads(self.config_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Configuration JSON invalide dans {self.config_file}: {exc}") from exc
        except OSError as exc:
            raise RuntimeError(f"Impossible de lire la configuration {self.config_file}: {exc}") from exc

        payload = settings.to_dict()
        payload.update(content)
        merged = AppSettings(**payload)
        self.apply_profile_defaults(merged)
        return merged

    def save(self, settings: AppSettings) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.config_file.write_text(
                json.dumps(settings.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise RuntimeError(f"Impossible d'ecrire la configuration {self.config_file}: {exc}") from exc

    def apply_profile_defaults(self, settings: AppSettings) -> None:
        preset = PROFILE_PRESETS.get(settings.security_profile)
        if not preset:
            return
        settings.scan_interval_seconds = int(preset["scan_interval_seconds"])
        settings.alert_threshold = int(preset["alert_threshold"])
        settings.dedup_window_seconds = int(preset["dedup_window_seconds"])
