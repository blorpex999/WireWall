from __future__ import annotations

from app.core.constants import USB_CLASS_MAP


class DeviceClassifier:
    def classify(
        self,
        usb_class: int | None,
        interface_classes: list[int] | None,
        vendor_name: str,
        product_name: str,
    ) -> tuple[str, str, float]:
        if usb_class in USB_CLASS_MAP:
            return USB_CLASS_MAP[usb_class], "usb_class", 0.9

        if interface_classes:
            for class_code in interface_classes:
                if class_code in USB_CLASS_MAP:
                    return USB_CLASS_MAP[class_code], "interface_class", 0.75

        name_blob = f"{vendor_name} {product_name}".lower()
        if any(token in name_blob for token in ("storage", "disk", "flash", "mass")):
            return "storage", "product_hint", 0.6
        if any(token in name_blob for token in ("keyboard", "mouse", "hid")):
            return "hid", "product_hint", 0.6
        if "hub" in name_blob:
            return "hub", "product_hint", 0.6
        if any(token in name_blob for token in ("camera", "image", "webcam")):
            return "imaging", "product_hint", 0.55
        if any(token in name_blob for token in ("modem", "serial", "com")):
            return "communication", "product_hint", 0.55

        return "unknown", "fallback", 0.35
