from __future__ import annotations

from dataclasses import replace

from app.core.classifier import DeviceClassifier
from app.models.entities import Alert, DeviceEvent, EnumerationResult, USBDevice
from app.utils.datetime import utc_now


class ModeSwitchingUsbEnumerator:
    def __init__(self, settings, real_enumerator, demo_enumerator) -> None:
        self.settings = settings
        self.real_enumerator = real_enumerator
        self.demo_enumerator = demo_enumerator

    def update_settings(self, settings) -> None:
        self.settings = settings

    @property
    def demo_mode(self) -> bool:
        return str(getattr(self.settings, "mode", "real")).lower() == "demo"

    def _active(self):
        return self.demo_enumerator if self.demo_mode else self.real_enumerator

    def backend_status(self) -> tuple[bool, str]:
        return self._active().backend_status()

    def enumerate(self) -> EnumerationResult:
        return self._active().enumerate()


class DemoUsbEnumerator:
    def __init__(self, classifier: DeviceClassifier) -> None:
        self.classifier = classifier
        self._step = 0
        self._snapshots = self._build_snapshots()

    def backend_status(self) -> tuple[bool, str]:
        return True, "Backend demo actif."

    def enumerate(self) -> EnumerationResult:
        snapshot = self._snapshots[self._step % len(self._snapshots)]
        self._step += 1
        return EnumerationResult(True, [replace(device) for device in snapshot], "Snapshot demo collecte.", {})

    def _build_snapshots(self) -> list[list[USBDevice]]:
        keyboard = USBDevice(
            device_key="046D:C31C:DEMO-KB-001",
            vid=0x046D,
            pid=0xC31C,
            vendor_name="LogiDemo",
            product_name="USB Keyboard",
            serial_number="DEMO-KB-001",
            usb_class=0x03,
            category="hid",
            confidence=0.95,
            identification_source="demo",
            source_backend="demo",
            demo_mode=True,
        )
        storage = USBDevice(
            device_key="0781:5581:DEMO-ST-999",
            vid=0x0781,
            pid=0x5581,
            vendor_name="SanDemo",
            product_name="Mass Storage",
            serial_number="DEMO-ST-999",
            usb_class=0x08,
            category="storage",
            confidence=0.95,
            identification_source="demo",
            source_backend="demo",
            demo_mode=True,
        )
        imaging = USBDevice(
            device_key="1BCF:2C9B:DEMO-CAM-123",
            vid=0x1BCF,
            pid=0x2C9B,
            vendor_name="DemoCam",
            product_name="USB Camera",
            serial_number="DEMO-CAM-123",
            usb_class=0x06,
            category="imaging",
            confidence=0.9,
            identification_source="demo",
            source_backend="demo",
            demo_mode=True,
        )
        return [
            [keyboard],
            [keyboard, storage],
            [keyboard, imaging],
            [keyboard, storage, imaging],
        ]


class DemoDataService:
    DEMO_POLICY_MARKER = "[demo_only]"

    def seed(self, policy_service, alert_repo, event_repo) -> None:
        now = utc_now()
        self._ensure_policy(
            policy_service,
            policy_type="whitelist",
            match_type="vid_pid",
            value="046D:C31C",
            label="Clavier de demonstration",
            notes=f"{self.DEMO_POLICY_MARKER} Autorise pour la soutenance.",
        )
        self._ensure_policy(
            policy_service,
            policy_type="blacklist",
            match_type="serial",
            value="DEMO-ST-999",
            label="Cle USB suspecte",
            notes=f"{self.DEMO_POLICY_MARKER} Exemple de media amovible non autorise.",
        )

        recent_demo_events = event_repo.list_recent(limit=50, demo_mode=True)
        if not any(event.event_type == "demo_seed" for event in recent_demo_events):
            event_repo.add(
                DeviceEvent(
                    occurred_at=now,
                    event_type="demo_seed",
                    device_key=None,
                    summary="Jeu de donnees de demonstration initialise.",
                    severity="INFO",
                    source="demo",
                    demo_mode=True,
                )
            )

        demo_alerts = alert_repo.list_all(demo_mode=True)
        if not any(alert.title == "Alerte demo" for alert in demo_alerts):
            alert_repo.add(
                Alert(
                    created_at=now,
                    severity="HIGH",
                    title="Alerte demo",
                    message="Une cle USB de demonstration suspecte sera injectee lors du scenario.",
                    recommendations=["Utiliser le bouton d'analyse IA pour commenter la situation."],
                    demo_mode=True,
                )
            )

    def _ensure_policy(self, policy_service, **kwargs) -> None:
        existing = policy_service.list_entries(policy_type=kwargs["policy_type"], query=kwargs["value"])
        if any(entry.match_type == kwargs["match_type"] and entry.value == kwargs["value"] for entry in existing):
            return
        policy_service.add_entry(**kwargs)
