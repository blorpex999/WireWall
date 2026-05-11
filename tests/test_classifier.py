from __future__ import annotations

from app.core.classifier import DeviceClassifier


def test_classifier_by_usb_class() -> None:
    classifier = DeviceClassifier()
    category, source, confidence = classifier.classify(0x08, [], "Vendor", "Product")
    assert category == "storage"
    assert source == "usb_class"
    assert confidence > 0.8


def test_classifier_by_product_hint() -> None:
    classifier = DeviceClassifier()
    category, source, confidence = classifier.classify(None, [], "Unknown", "USB Keyboard")
    assert category == "hid"
    assert source == "product_hint"
    assert confidence >= 0.5


def test_classifier_enriches_sonix_camera_identity() -> None:
    classifier = DeviceClassifier()
    category, source, confidence = classifier.classify(None, [0x0E], "SONiX", "USB DEVICE")
    identity = classifier.enrich_identity(
        vid=0x0C45,
        pid=0x636B,
        usb_class=0,
        interface_classes=[0x0E],
        vendor_name="SONiX",
        product_name="USB DEVICE",
        category=category,
        source=source,
    )

    assert category == "imaging"
    assert identity["vendor_name"] == "Sonix Technology"
    assert "Camera" in identity["product_name"]
    assert "webcams" in identity["description"]
    assert "Interface classe video" in identity["identity_hints"]
    assert confidence >= 0.7


def test_classifier_enriches_generic_storage_identity() -> None:
    classifier = DeviceClassifier()
    category, source, _confidence = classifier.classify(0x08, [], "Unknown", "USB Device")
    identity = classifier.enrich_identity(
        vid=0x0781,
        pid=0x5567,
        usb_class=0x08,
        interface_classes=[],
        vendor_name="Unknown",
        product_name="USB Device",
        category=category,
        source=source,
    )

    assert identity["vendor_name"] == "SanDisk"
    assert identity["product_name"] == "Support de stockage USB"
    assert "stockage" in identity["description"]


def test_classifier_enriches_apple_mobile_device_identity() -> None:
    classifier = DeviceClassifier()
    category, source, confidence = classifier.classify(0, [0x06, 0xFF], "Apple", "Apple iPhone")
    identity = classifier.enrich_identity(
        vid=0x05AC,
        pid=0x12A8,
        usb_class=0,
        interface_classes=[0x06, 0xFF],
        vendor_name="Apple",
        product_name="Apple iPhone",
        category=category,
        source=source,
    )

    assert category == "communication"
    assert source == "product_hint"
    assert confidence >= 0.7
    assert identity["vendor_name"] == "Apple"
    assert identity["product_name"] == "Apple iPhone"
    assert "iOS" in identity["description"]


def test_classifier_labels_generic_apple_mobile_device_from_vid_pid() -> None:
    classifier = DeviceClassifier()
    category, source, _confidence = classifier.classify(0, [0xFF], "Unknown", "USB Device")
    identity = classifier.enrich_identity(
        vid=0x05AC,
        pid=0x12A8,
        usb_class=0,
        interface_classes=[0xFF],
        vendor_name="Unknown",
        product_name="USB Device",
        category=category,
        source=source,
    )

    assert identity["vendor_name"] == "Apple"
    assert identity["product_name"] == "iPhone / iPad (Apple Mobile Device)"
    assert "iOS" in identity["description"]
