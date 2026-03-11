from __future__ import annotations

import re


VID_PID_PATTERN = re.compile(r"^[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4}$")


def normalize_vid_pid(value: str) -> str:
    return value.strip().upper()


def is_valid_vid_pid(value: str) -> bool:
    return bool(VID_PID_PATTERN.match(normalize_vid_pid(value)))


def normalize_serial(value: str) -> str:
    return value.strip()


def ensure_non_empty(value: str, fallback: str = "") -> str:
    text = value.strip()
    return text if text else fallback
