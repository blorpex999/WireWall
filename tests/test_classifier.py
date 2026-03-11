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
