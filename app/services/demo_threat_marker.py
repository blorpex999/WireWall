from __future__ import annotations

import ctypes
import os
import string
from dataclasses import dataclass
from pathlib import Path


DEMO_THREAT_MARKER_NAMES = (
    "WIREWALL_DEMO_THREAT.txt",
    "WIREWALL_ATTACK_SIMULATION.txt",
    "wirewall_demo_payload.bat",
    "wirewall_demo_payload.ps1",
    "wirewall_demo_payload.exe",
)


@dataclass(frozen=True, slots=True)
class DemoThreatMarker:
    drive_root: str
    marker_path: str
    marker_name: str


class DemoThreatMarkerScanner:
    def __init__(self, roots: list[Path] | None = None, marker_names: tuple[str, ...] = DEMO_THREAT_MARKER_NAMES) -> None:
        self.roots = roots
        self.marker_names = marker_names

    def scan(self) -> list[DemoThreatMarker]:
        markers: list[DemoThreatMarker] = []
        for root in self._candidate_roots():
            for marker_name in self.marker_names:
                marker_path = root / marker_name
                try:
                    if marker_path.is_file():
                        markers.append(
                            DemoThreatMarker(
                                drive_root=str(root),
                                marker_path=str(marker_path),
                                marker_name=marker_name,
                            )
                        )
                except OSError:
                    continue
        return markers

    def _candidate_roots(self) -> list[Path]:
        if self.roots is not None:
            return self.roots
        if os.name != "nt":
            return []
        return self._windows_drive_roots()

    def _windows_drive_roots(self) -> list[Path]:
        try:
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        except Exception:
            return []
        roots: list[Path] = []
        for index, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << index):
                roots.append(Path(f"{letter}:\\"))
        return roots
