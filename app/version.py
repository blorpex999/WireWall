from __future__ import annotations

import sys
from pathlib import Path


def get_version() -> str:
    for candidate in _candidate_paths():
        try:
            value = candidate.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if value:
            return value
    return "0.0.0"


def _candidate_paths() -> list[Path]:
    paths: list[Path] = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            paths.append(Path(meipass) / "VERSION")
        paths.append(Path(sys.executable).resolve().parent / "VERSION")
    paths.append(Path(__file__).resolve().parents[1] / "VERSION")
    return paths


__version__ = get_version()
