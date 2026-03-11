from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppPaths:
    root_dir: Path
    data_dir: Path
    demo_dir: Path
    logs_dir: Path
    exports_dir: Path
    config_dir: Path
    config_file: Path
    demo_db_path: Path
    db_path: Path

    def ensure(self) -> None:
        for path in (
            self.root_dir,
            self.data_dir,
            self.demo_dir,
            self.logs_dir,
            self.exports_dir,
            self.config_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


def build_app_paths(app_name: str = "WireWall", base_dir: Path | None = None) -> AppPaths:
    preferred_base = base_dir
    if preferred_base is None:
        override = os.environ.get("WIREWALL_HOME")
        if override:
            preferred_base = Path(override)
        else:
            preferred_base = Path(os.environ.get("LOCALAPPDATA", Path.cwd() / ".wirewall"))
    root_dir = preferred_base / app_name
    data_dir = root_dir / "data"
    demo_dir = root_dir / "demo"
    logs_dir = root_dir / "logs"
    exports_dir = root_dir / "exports"
    config_dir = root_dir / "config"
    return AppPaths(
        root_dir=root_dir,
        data_dir=data_dir,
        demo_dir=demo_dir,
        logs_dir=logs_dir,
        exports_dir=exports_dir,
        config_dir=config_dir,
        config_file=config_dir / "config.json",
        db_path=data_dir / "wirewall.db",
        demo_db_path=demo_dir / "wirewall_demo.db",
    )
