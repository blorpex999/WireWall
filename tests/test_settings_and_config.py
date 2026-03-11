from __future__ import annotations

import pytest

from app.infrastructure.config_loader import ConfigLoader


def test_config_loader_applies_profile_defaults(workspace_tmp_dir) -> None:
    config_path = workspace_tmp_dir / "config.json"
    config_path.write_text(
        """
        {
          "security_profile": "Strict",
          "ollama_model": "mistral"
        }
        """,
        encoding="utf-8",
    )
    loader = ConfigLoader(config_path)
    settings = loader.load()
    assert settings.security_profile == "Strict"
    assert settings.scan_interval_seconds == 1
    assert settings.alert_threshold == 35
    assert settings.ollama_model == "mistral"


def test_config_loader_returns_defaults_when_file_is_missing(workspace_tmp_dir) -> None:
    loader = ConfigLoader(workspace_tmp_dir / "missing.json")
    settings = loader.load()
    assert settings.security_profile == "Normal"
    assert settings.scan_interval_seconds == 2


def test_config_loader_raises_runtime_error_for_invalid_json(workspace_tmp_dir) -> None:
    config_path = workspace_tmp_dir / "config.json"
    config_path.write_text("{ invalid json", encoding="utf-8")
    loader = ConfigLoader(config_path)

    with pytest.raises(RuntimeError, match="Configuration JSON invalide"):
        loader.load()
