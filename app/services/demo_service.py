from __future__ import annotations

from dataclasses import replace

from app.core.classifier import DeviceClassifier
from app.models.entities import Alert, DeviceEvent, EnumerationResult, USBDevice
from app.utils.datetime import utc_now


class DemoUsbEnumerator:
    def __init__(self, classifier: DeviceClassifier) -> None:
        self.classifier = classifier
        self._step = 0
        self._snapshots = self._build_snapshots()

    def backend_status(self) -> tuple[bool, str]:
        return True, "Backend démo actif."

    def enumerate(self) -> EnumerationResult:
        snapshot = self._snapshots[self._step % len(self._snapshots)]
        self._step += 1
        return EnumerationResult(True, [replace(device) for device in snapshot], "Snapshot démo collecté.", {})

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
    def seed(self, policy_service, alert_repo, event_repo) -> None:
        if policy_service.list_entries():
            return

        now = utc_now()
        policy_service.add_entry(
            policy_type="whitelist",
            match_type="vid_pid",
            value="046D:C31C",
            label="Clavier de démonstration",
            notes="Autorisé pour la soutenance",
        )
        policy_service.add_entry(
            policy_type="blacklist",
            match_type="serial",
            value="DEMO-ST-999",
            label="Clé USB suspecte",
            notes="Exemple de média amovible non autorisé",
        )
        event_repo.add(
            DeviceEvent(
                occurred_at=now,
                event_type="demo_seed",
                device_key=None,
                summary="Jeu de données de démonstration initialisé.",
                severity="INFO",
                source="demo",
                demo_mode=True,
            )
        )
        alert_repo.add(
            Alert(
                created_at=now,
                severity="HIGH",
                title="Alerte démo",
                message="Une clé USB de démonstration suspecte sera injectée lors du scénario.",
                recommendations=["Utiliser le bouton d'analyse IA pour commenter la situation."],
                demo_mode=True,
            )
        )
