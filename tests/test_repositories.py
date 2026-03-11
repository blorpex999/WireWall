from __future__ import annotations

from app.models.entities import DeviceEvent, USBDevice


def test_device_and_event_repository_roundtrip(repositories) -> None:
    device_repo = repositories["device_repo"]
    event_repo = repositories["event_repo"]

    device = USBDevice(
        device_key="1234:5678:ABC",
        vid=0x1234,
        pid=0x5678,
        vendor_name="Vendor",
        product_name="Product",
        serial_number="ABC",
        category="storage",
        first_seen="2026-03-11T10:00:00+00:00",
        last_seen="2026-03-11T10:00:00+00:00",
    )
    device_repo.upsert(device)
    stored = device_repo.get(device.device_key)
    assert stored is not None
    assert stored.vid_pid == "1234:5678"

    event_id = event_repo.add(
        DeviceEvent(
            occurred_at="2026-03-11T10:00:00+00:00",
            event_type="connected",
            device_key=device.device_key,
            summary="Device connected",
            severity="LOW",
            source="test",
        )
    )
    assert event_id > 0
    recent = event_repo.list_recent()
    assert len(recent) == 1
    assert recent[0].event_type == "connected"
