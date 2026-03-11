from __future__ import annotations

from app.models.entities import Alert, DeviceEvent, HealthStatus, USBDevice
from app.services.brain_service import BrainService
from app.utils.datetime import utc_now


def test_brain_service_detects_deterioration_and_persists_snapshot(repositories) -> None:
    repositories["device_repo"].upsert(
        USBDevice(
            device_key="046D:C539",
            vid=0x046D,
            pid=0xC539,
            vendor_name="Logitech",
            product_name="USB Receiver",
            category="hid",
            status="connected",
            risk_level="LOW",
            risk_score=15,
            first_seen=utc_now(),
            last_seen=utc_now(),
        )
    )
    repositories["health_repo"].replace_all([HealthStatus("ollama", "ok", "ready", utc_now())])

    service = BrainService(
        repositories["device_repo"],
        repositories["event_repo"],
        repositories["alert_repo"],
        repositories["health_repo"],
        repositories["ai_repo"],
        repositories["brain_repo"],
    )

    initial = service.refresh(False)
    assert initial.progress_status == "LEARNING"
    assert initial.global_level == "LOW"

    repositories["device_repo"].upsert(
        USBDevice(
            device_key="1234:5678:SUSPECT",
            vid=0x1234,
            pid=0x5678,
            vendor_name="Unknown",
            product_name="USB Device",
            category="storage",
            status="connected",
            risk_level="HIGH",
            risk_score=82,
            first_seen=utc_now(),
            last_seen=utc_now(),
        )
    )
    repositories["event_repo"].add(
        DeviceEvent(
            occurred_at=utc_now(),
            event_type="connected",
            device_key="1234:5678:SUSPECT",
            summary="Suspicious device connected",
            severity="HIGH",
            score=82,
            level="HIGH",
            source="test",
        )
    )
    repositories["alert_repo"].add(
        Alert(
            created_at=utc_now(),
            severity="CRITICAL",
            title="Alerte critique",
            message="Device blacklisted or highly suspicious",
            device_key="1234:5678:SUSPECT",
            score=90,
        )
    )

    degraded = service.refresh(False)

    assert degraded.global_level == "CRITICAL"
    assert degraded.progress_status == "DETERIORATING"
    assert degraded.incident_count >= 1
    assert degraded.open_alert_count == 1
    assert "incident" in degraded.summary.lower()
    assert repositories["brain_repo"].latest(False).global_level == "CRITICAL"


def test_brain_service_skips_duplicate_snapshot_when_state_is_unchanged(repositories) -> None:
    repositories["device_repo"].upsert(
        USBDevice(
            device_key="046D:C539",
            vid=0x046D,
            pid=0xC539,
            vendor_name="Logitech",
            product_name="USB Receiver",
            category="hid",
            status="connected",
            risk_level="LOW",
            risk_score=10,
            first_seen=utc_now(),
            last_seen=utc_now(),
        )
    )

    service = BrainService(
        repositories["device_repo"],
        repositories["event_repo"],
        repositories["alert_repo"],
        repositories["health_repo"],
        repositories["ai_repo"],
        repositories["brain_repo"],
    )

    first = service.refresh(False)
    second = service.refresh(False)
    before = repositories["brain_repo"].list_recent(False, limit=10)
    latest = service.refresh(False)
    after = repositories["brain_repo"].list_recent(False, limit=10)

    assert first.progress_status == "LEARNING"
    assert second.progress_status == "STABLE"
    assert len(before) == len(after)
    assert latest.id == second.id
