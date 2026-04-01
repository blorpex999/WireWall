from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse


VID_PID_PATTERN = re.compile(r"^[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4}$")
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n", "＝", "＋", "－", "＠")


def normalize_vid_pid(value: str) -> str:
    return value.strip().upper()


def is_valid_vid_pid(value: str) -> bool:
    return bool(VID_PID_PATTERN.match(normalize_vid_pid(value)))


def normalize_serial(value: str) -> str:
    return value.strip()


def ensure_non_empty(value: str, fallback: str = "") -> str:
    text = value.strip()
    return text if text else fallback


def is_local_http_url(value: str) -> bool:
    raw = value.strip()
    if not raw:
        return False

    candidate = raw if "://" in raw else f"http://{raw}"
    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in {"", "http"}:
        return False
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return False
    if parsed.path not in {"", "/"}:
        return False

    host = parsed.hostname
    if not host:
        return False
    if host.lower() == "localhost":
        return True

    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def sanitize_csv_cell(value: object) -> object:
    if not isinstance(value, str):
        return value
    if value.startswith(CSV_FORMULA_PREFIXES):
        return f"\t{value}"
    return value
