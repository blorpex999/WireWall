from __future__ import annotations

from app.models.entities import OperationResult
from app.services import usb_control_service as control_module
from app.services.usb_control_service import UsbControlService


class FakeRegistry:
    def __init__(self, status="enabled") -> None:
        self.status = status
        self.services = {"USBXHCI": 3, "USBHUB3": 3, "usbhub": 3, "UCX01000": 3}
        self.backup = {}

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
    service = UsbControlService(registry)

    block = service.block_all_usb_ports()
    assert block.success is True
    assert block.status == "blocked"
    assert all(value == 4 for value in registry.services.values())

    restore = service.restore_all_usb_ports()
    assert restore.success is True
    assert restore.status == "enabled"
    assert registry.services["USBXHCI"] == 3
    assert registry.services["USBHUB3"] == 2
