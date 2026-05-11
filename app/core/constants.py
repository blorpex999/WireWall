from __future__ import annotations

RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
USB_CATEGORIES = (
    "storage",
    "hid",
    "hub",
    "imaging",
    "communication",
    "audio_video",
    "vendor_specific",
    "unknown",
)

USB_CLASS_MAP = {
    0x08: "storage",
    0x03: "hid",
    0x09: "hub",
    0x06: "imaging",
    0x0E: "imaging",
    0x01: "audio_video",
    0x02: "communication",
    0x0A: "communication",
    0xE0: "communication",
    0xFF: "vendor_specific",
}

LOW_MAX = 24
MEDIUM_MAX = 49
HIGH_MAX = 74
