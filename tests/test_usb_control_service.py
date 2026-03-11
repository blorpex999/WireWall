from __future__ import annotations

from app.models.entities import OperationResult
from app.services import usb_control_service as control_module
from app.services.usb_control_service import UsbControlService


class FakeRegistry:
    def __init__(self, status="enabled") -> None:
        self.status = status

    def get_usbstor_start(self):
        return OperationResult(True, self.status, "ok", {"start_value": 3 if self.status == "enabled" else 4})

    def set_usbstor_start(self, value: int):
        self.status = "blocked" if value == 4 else "enabled"
        return OperationResult(True, self.status, "changed", {"start_value": value})


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
