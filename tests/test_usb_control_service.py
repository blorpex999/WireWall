from __future__ import annotations

from app.models.entities import OperationResult
from app.services import usb_control_service as control_module
from app.services.usb_control_service import UsbControlService


class FakeRegistry:
    def __init__(self, status="enabled") -> None:
        self.status = status
        self.services = {"USBXHCI": 3, "USBHUB3": 3, "usbhub": 3, "UCX01000": 3}
        self.backup = {}
        self.pnp_backup = []

    def get_usbstor_start(self):
        return OperationResult(True, self.status, "ok", {"start_value": 3 if self.status == "enabled" else 4})

    def set_usbstor_start(self, value: int):
        self.status = "blocked" if value == 4 else "enabled"
        return OperationResult(True, self.status, "changed", {"start_value": value})

    def get_service_start(self, service_name: str):
        if service_name not in self.services:
            return OperationResult(False, "not_found", "missing")
        return OperationResult(True, "read", "ok", {"service": service_name, "start_value": self.services[service_name]})

    def set_service_start(self, service_name: str, value: int):
        if service_name not in self.services:
            return OperationResult(False, "not_found", "missing")
        self.services[service_name] = value
        return OperationResult(True, "changed", "changed", {"service": service_name, "start_value": value})

    def save_usb_lockdown_backup(self, values: dict[str, int]):
        self.backup = dict(values)
        return OperationResult(True, "saved", "saved", {"backup": self.backup})

    def load_usb_lockdown_backup(self):
        if not self.backup:
            return OperationResult(False, "not_found", "missing")
        return OperationResult(True, "loaded", "loaded", {"backup": self.backup})

    def save_usb_lockdown_pnp_backup(self, instance_ids: list[str]):
        self.pnp_backup = list(instance_ids)
        return OperationResult(True, "saved", "saved", {"instance_ids": self.pnp_backup})

    def load_usb_lockdown_pnp_backup(self):
        if not self.pnp_backup:
            return OperationResult(False, "not_found", "missing")
        return OperationResult(True, "loaded", "loaded", {"instance_ids": self.pnp_backup})

    def apply_usb_lockdown_policies(self, class_guids: list[str]):
        return OperationResult(True, "applied", "applied", {"classes": class_guids})

    def restore_usb_lockdown_policies(self):
        return OperationResult(True, "restored", "restored", {"backup_used": True})

    def load_usb_lockdown_policy_backup(self):
        return OperationResult(False, "not_found", "missing")


class FakePnpDeviceManager:
    def __init__(self) -> None:
        self.devices = [
            {"instance_id": r"USBSTOR\DISK&VEN_TEST\123", "name": "Disque USB", "class": "DiskDrive", "status": "OK"},
            {"instance_id": r"HID\VID_046D&PID_C077\456", "name": "Souris USB", "class": "HIDClass", "status": "OK"},
        ]
        self.disabled = []
        self.enabled = []

    def list_lockdown_candidates(self):
        return OperationResult(True, "ok", "ok", {"devices": self.devices})

    def disable_devices(self, instance_ids: list[str]):
        self.disabled = list(instance_ids)
        return OperationResult(True, "disabled", "disabled", {"changed": self.disabled, "failed": {}})

    def enable_devices(self, instance_ids: list[str]):
        self.enabled = list(instance_ids)
        return OperationResult(True, "enabled", "enabled", {"changed": self.enabled, "failed": {}})

    def apply_policy_refresh(self):
        return OperationResult(True, "ok", "ok", {"output": "ok"})

    def disable_usb_device_ids(self):
        return OperationResult(True, "disabled", "disabled", {"changed": ["USB\\Class_08"], "failed": {}})


def test_usb_control_requires_admin(monkeypatch) -> None:
    monkeypatch.setattr(control_module, "is_admin", lambda: False)
    service = UsbControlService(FakeRegistry())
    result = service.block_storage()
    assert result.success is False
    assert result.status == "permission_denied"


def test_usb_control_block_success(monkeypatch) -> None:
    monkeypatch.setattr(control_module, "is_admin", lambda: True)
    service = UsbControlService(FakeRegistry())
    result = service.block_storage()
    assert result.success is True
    assert result.status == "blocked"


def test_usb_control_full_lockdown_saves_and_restores_services(monkeypatch) -> None:
    monkeypatch.setattr(control_module, "is_admin", lambda: True)
    registry = FakeRegistry()
    registry.services["USBHUB3"] = 2
    pnp = FakePnpDeviceManager()
    service = UsbControlService(registry, pnp)

    block = service.block_all_usb_ports()
    assert block.success is True
    assert block.status == "blocked"
    assert all(value == 4 for value in registry.services.values())
    assert pnp.disabled == [r"USBSTOR\DISK&VEN_TEST\123", r"HID\VID_046D&PID_C077\456"]

    restore = service.restore_all_usb_ports()
    assert restore.success is True
    assert restore.status == "enabled"
    assert registry.services["USBXHCI"] == 3
    assert registry.services["USBHUB3"] == 2
    assert pnp.enabled == [r"USBSTOR\DISK&VEN_TEST\123", r"HID\VID_046D&PID_C077\456"]
