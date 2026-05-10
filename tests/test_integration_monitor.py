from __future__ import annotations

from app.config.defaults import build_default_settings
from app.core.risk_engine import RiskEngine
from app.models.entities import EnumerationResult, USBDevice
from app.services.baseline_service import BaselineService
from app.services.demo_threat_marker import DemoThreatMarker
from app.services.event_bus import EventBus
from app.services.incident_service import IncidentService
from app.services.policy_service import PolicyService
from app.services.usb_monitor import UsbMonitorService


class FakeEnumerator:
    def __init__(self, snapshots):
        self.snapshots = snapshots
        self.index = 0

    def backend_status(self):
        return True, "ok"

    def enumerate(self):
        current = self.snapshots[min(self.index, len(self.snapshots) - 1)]
        self.index += 1
        return current


class FakeMarkerScanner:
    def __init__(self, markers=None):
        self.markers = markers or []

    def scan(self):
        return self.markers


def build_monitor(repositories, snapshots, marker_scanner=None):
    settings = build_default_settings()
    settings.mode = "demo"
    settings.export_directory = ""
    policy_service = PolicyService(repositories["policy_repo"], repositories["device_repo"])
    incident_service = IncidentService(
        incident_repo=repositories["incident_repo"],
        alert_repo=repositories["alert_repo"],
        policy_service=policy_service,
        device_repo=repositories["device_repo"],
        operator_name_getter=lambda: "Tests",
    )
    bus = EventBus()
    monitor = UsbMonitorService(
        enumerator=FakeEnumerator(snapshots),
        device_repo=repositories["device_repo"],
        event_repo=repositories["event_repo"],
        assessment_repo=repositories["assessment_repo"],
        alert_repo=repositories["alert_repo"],
        policy_service=policy_service,
        risk_engine=RiskEngine(),
        baseline_service=BaselineService(),
        incident_service=incident_service,
        event_bus=bus,
        settings=settings,
        demo_threat_marker_scanner=marker_scanner,
    )
    return monitor, bus


def test_monitor_connect_disconnect_pipeline(repositories) -> None:
    device = USBDevice(
        device_key="1234:5678:TEST",
        vid=0x1234,
        pid=0x5678,
        vendor_name="Vendor",
        product_name="Mass Storage",
        serial_number="TEST",
        category="storage",
        demo_mode=True,
    )
    monitor, _bus = build_monitor(
        repositories,
        [
            EnumerationResult(True, [device], "ok", {}),
            EnumerationResult(True, [], "ok", {}),
        ],
    )

    monitor.scan_once()
    devices = repositories["device_repo"].list_all(demo_mode=True)
    assert len(devices) == 1
    assert devices[0].status == "connected"

    monitor.scan_once()
    devices = repositories["device_repo"].list_all(demo_mode=True)
    events = repositories["event_repo"].list_recent(demo_mode=True)
    assert devices[0].status == "disconnected"
    assert any(event.event_type == "connected" for event in events)
    assert any(event.event_type == "disconnected" for event in events)


def test_monitor_keeps_snapshot_when_enumeration_fails(repositories) -> None:
    device = USBDevice(
        device_key="1234:5678:TEST",
        vid=0x1234,
        pid=0x5678,
        vendor_name="Vendor",
        product_name="Mass Storage",
        serial_number="TEST",
        category="storage",
        demo_mode=True,
    )
    monitor, bus = build_monitor(
        repositories,
        [
            EnumerationResult(True, [device], "ok", {}),
            EnumerationResult(False, [], "scan failed", {"backend_status": "offline"}),
        ],
    )

    assert monitor.scan_once() is True
    assert monitor.scan_once() is False

    stored = repositories["device_repo"].get(device.device_key)
    events = repositories["event_repo"].list_recent(demo_mode=True)
    drained = bus.drain()

    assert stored is not None
    assert stored.status == "connected"
    assert any(event.event_type == "connected" for event in events)
    assert any(event.event_type == "scan_error" for event in events)
    assert all(event.event_type != "disconnected" for event in events)
    assert any(item["type"] == "monitor_warning" for item in drained)


def test_monitor_creates_demo_attack_alert_from_usb_marker(repositories) -> None:
    monitor, bus = build_monitor(
        repositories,
        [EnumerationResult(True, [], "ok", {})],
        marker_scanner=FakeMarkerScanner(
            [
                DemoThreatMarker(
                    drive_root="E:\\",
                    marker_path="E:\\WIREWALL_DEMO_THREAT.txt",
                    marker_name="WIREWALL_DEMO_THREAT.txt",
                )
            ]
        ),
    )

    assert monitor.scan_once() is True

    events = repositories["event_repo"].list_recent(demo_mode=True)
    alerts = repositories["alert_repo"].list_all(demo_mode=True)
    drained = bus.drain()

    assert any(event.event_type == "demo_threat_marker_detected" for event in events)
    assert any(alert.title == "Simulation d'attaque USB" for alert in alerts)
    assert any(item["type"] == "alert_created" for item in drained)


def test_monitor_reuses_inventory_row_for_reconnected_device_without_serial(repositories) -> None:
    disconnected_key = "046D:C539:1:4"
    reconnected_key = "046D:C539:1:7"
    first_snapshot_device = USBDevice(
        device_key=disconnected_key,
        vid=0x046D,
        pid=0xC539,
        vendor_name="Logitech",
        product_name="USB Receiver",
        serial_number=None,
        category="hid",
        demo_mode=True,
    )
    second_snapshot_device = USBDevice(
        device_key=reconnected_key,
        vid=0x046D,
        pid=0xC539,
        vendor_name="Logitech",
        product_name="USB Receiver",
        serial_number=None,
        category="hid",
        demo_mode=True,
    )
    monitor, _bus = build_monitor(
        repositories,
        [
            EnumerationResult(True, [first_snapshot_device], "ok", {}),
            EnumerationResult(True, [], "ok", {}),
            EnumerationResult(True, [second_snapshot_device], "ok", {}),
        ],
    )

    assert monitor.scan_once() is True
    assert monitor.scan_once() is True
    assert monitor.scan_once() is True

    devices = repositories["device_repo"].list_all(demo_mode=True)
    events = repositories["event_repo"].list_recent(demo_mode=True)

    assert len(devices) == 1
    assert devices[0].device_key == disconnected_key
    assert devices[0].status == "connected"
    assert any(event.event_type == "disconnected" for event in events)
    assert any(event.event_type == "connected" for event in events)
    assert all(event.device_key == disconnected_key for event in events if event.device_key)


def test_monitor_preserves_richer_metadata_when_reconnect_returns_generic_labels(repositories) -> None:
    first_key = "046D:C539:1:6"
    reconnect_key = "046D:C539:1:7"
    first_snapshot_device = USBDevice(
        device_key=first_key,
        vid=0x046D,
        pid=0xC539,
        vendor_name="Logitech",
        product_name="USB Receiver",
        serial_number=None,
        category="hid",
        confidence=0.9,
        identification_source="usb_class",
        demo_mode=True,
    )
    reconnect_snapshot_device = USBDevice(
        device_key=reconnect_key,
        vid=0x046D,
        pid=0xC539,
        vendor_name="Inconnu",
        product_name="Périphérique USB",
        serial_number=None,
        category="hid",
        confidence=0.4,
        identification_source="fallback",
        demo_mode=True,
    )
    monitor, _bus = build_monitor(
        repositories,
        [
            EnumerationResult(True, [first_snapshot_device], "ok", {}),
            EnumerationResult(True, [], "ok", {}),
            EnumerationResult(True, [reconnect_snapshot_device], "ok", {}),
        ],
    )

    assert monitor.scan_once() is True
    assert monitor.scan_once() is True
    assert monitor.scan_once() is True

    devices = repositories["device_repo"].list_all(demo_mode=True)

    assert len(devices) == 1
    assert devices[0].device_key == first_key
    assert devices[0].vendor_name == "Logitech"
    assert devices[0].product_name == "USB Receiver"
    assert devices[0].status == "connected"
