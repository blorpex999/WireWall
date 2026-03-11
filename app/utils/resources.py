from __future__ import annotations

import sys
from pathlib import Path


def asset_path(*parts: str) -> Path:
    for base in _candidate_bases():
        candidate = base.joinpath(*parts)
        if candidate.exists():
            return candidate
    return _candidate_bases()[-1].joinpath(*parts)


def _candidate_bases() -> list[Path]:
    paths: list[Path] = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            paths.append(Path(meipass))
        paths.append(Path(sys.executable).resolve().parent)
    paths.append(Path(__file__).resolve().parents[2])
    return paths
