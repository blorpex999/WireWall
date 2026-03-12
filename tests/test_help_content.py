from __future__ import annotations

from app.ui.help_content import GLOSSARY, SCREEN_HELP


def test_help_content_covers_core_views() -> None:
    expected = {"dashboard", "devices", "alerts", "usb_control", "ai_analysis", "about"}

    assert expected.issubset(SCREEN_HELP)
    for key in expected:
        sections = SCREEN_HELP[key]["sections"]
        assert len(sections) == 4
        assert all(len(section) == 2 for section in sections)


def test_glossary_contains_core_demo_terms() -> None:
    terms = {term for term, _definition in GLOSSARY}

    for required in {
        "USB",
        "VID/PID",
        "HID",
        "Hub",
        "Storage",
        "Serial",
        "Bus / Address",
        "PyUSB / libusb",
        "USBSTOR",
        "Baseline",
        "Incident",
        "Suggestion supervisee",
    }:
        assert required in terms
