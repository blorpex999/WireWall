from __future__ import annotations

from app.core.risk_engine import RiskEngine
from app.models.entities import USBDevice


def test_risk_engine_blacklisted_storage() -> None:
    engine = RiskEngine()
    device = USBDevice(
        device_key="1234:5678:SERIAL",
        vid=0x1234,
        pid=0x5678,
        vendor_name="Vendor",
        product_name="Mass Storage",
        serial_number="SERIAL",
        category="storage",
    )
    assessment = engine.assess(
        device=device,
        recent_events=[],
        policies={"is_blacklisted": True, "is_whitelisted": False, "is_known_device": False},
        profile="Normal",
        now="2026-03-11T22:30:00+00:00",
    )
    assert assessment.score >= 90
    assert assessment.level == "CRITICAL"
    assert any("blacklist" in reason.lower() for reason in assessment.reasons)


def test_risk_engine_whitelisted_known_device_reduces_score() -> None:
    engine = RiskEngine()
    device = USBDevice(
        device_key="1111:2222:SERIAL",
        vid=0x1111,
        pid=0x2222,
        vendor_name="Vendor",
        product_name="USB Keyboard",
        serial_number="SERIAL",
        category="hid",
    )
    assessment = engine.assess(
        device=device,
        recent_events=[],
        policies={"is_blacklisted": False, "is_whitelisted": True, "is_known_device": True},
        profile="Normal",
        now="2026-03-11T10:00:00+00:00",
    )
    assert assessment.score == 0
    assert assessment.level == "LOW"
