from __future__ import annotations

from app.core.classifier import DeviceClassifier
from app.services.usb_enumerator import UsbEnumerator


def test_windows_pnp_hint_prefers_user_friendly_apple_device_name() -> None:
    enumerator = UsbEnumerator(DeviceClassifier())
    hints = {
        (0x05AC, 0x12A8): [
            {
                "friendly_name": "Apple Mobile Device USB Composite Device",
                "instance_id": "USB\\VID_05AC&PID_12A8\\00008110001C450A1112801E",
                "pnp_class": "USB",
            },
            {
                "friendly_name": "Apple iPhone",
                "instance_id": "USB\\VID_05AC&PID_12A8&MI_00\\7&111&0&0000",
                "pnp_class": "WPD",
            },
        ]
    }

    selected = enumerator._match_windows_pnp_hint(hints, 0x05AC, 0x12A8, "00008110001C450A1112801E")

    assert selected is not None
    assert selected["friendly_name"] == "Apple iPhone"


def test_windows_pnp_name_replaces_generic_usb_product() -> None:
    enumerator = UsbEnumerator(DeviceClassifier())

    assert enumerator._should_use_pnp_name("USB Device", "Apple iPhone") is True
    assert enumerator._should_use_pnp_name("Mass Storage", "USB Composite Device") is False
