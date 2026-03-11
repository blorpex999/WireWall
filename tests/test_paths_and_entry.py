from __future__ import annotations

from types import SimpleNamespace

import main as main_module

import app.bootstrap as bootstrap_module
from app.infrastructure.paths import build_app_paths


def test_build_app_paths_uses_wirewall_home_override(monkeypatch, workspace_tmp_dir) -> None:
    override = workspace_tmp_dir / "custom-home"
    monkeypatch.setenv("WIREWALL_HOME", str(override))
    paths = build_app_paths()

    assert paths.root_dir == override / "WireWall"
    assert paths.db_path == override / "WireWall" / "data" / "wirewall.db"


def test_build_app_paths_falls_back_to_portable_dir(monkeypatch, workspace_tmp_dir) -> None:
    monkeypatch.delenv("WIREWALL_HOME", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.chdir(workspace_tmp_dir)

    paths = build_app_paths()

    assert paths.root_dir == workspace_tmp_dir / ".wirewall" / "WireWall"


def test_main_returns_error_and_notifies_when_tk_runtime_is_invalid(monkeypatch) -> None:
    notified: dict[str, str] = {}
    monkeypatch.setattr(main_module, "parse_args", lambda: SimpleNamespace(demo=False, config=None))
    monkeypatch.setattr(main_module, "validate_tk_runtime", lambda: (False, "Tk broken"))
    monkeypatch.setattr(main_module, "notify_startup_error", lambda message, title="WireWall": notified.setdefault("message", message))

    exit_code = main_module.main()

    assert exit_code == 1
    assert "Tk broken" in notified["message"]


def test_force_demo_does_not_persist_demo_mode_in_config(monkeypatch, workspace_tmp_dir) -> None:
    config_dir = workspace_tmp_dir / "WireWall" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"
    config_path.write_text(
        """
        {
          "mode": "real",
          "export_directory": ""
        }
        """,
        encoding="utf-8",
    )

    paths = build_app_paths(base_dir=workspace_tmp_dir)

    monkeypatch.setattr(bootstrap_module, "build_app_paths", lambda app_name: paths)

    container = bootstrap_module.build_container(force_demo=True)
    try:
        persisted = config_path.read_text(encoding="utf-8")
        assert '"mode": "real"' in persisted
        assert container.settings.mode == "demo"
    finally:
        container.shutdown()
