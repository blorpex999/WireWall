from __future__ import annotations

import logging
import sys
from pathlib import Path

from app.core.classifier import DeviceClassifier
from app.models.entities import EnumerationResult, USBDevice

LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover - depends on local environment
    import usb.core
    import usb.util
    from usb.backend import libusb1
except ImportError:  # pragma: no cover - dependency optional during tests
    usb = None
    libusb1 = None


class UsbEnumerator:
    def __init__(self, classifier: DeviceClassifier) -> None:
        self.classifier = classifier
        self.backend = self._resolve_backend()
        self.last_error = ""

    def backend_status(self) -> tuple[bool, str]:
        if libusb1 is None:
            return False, "PyUSB/libusb1 indisponible. Installer les dépendances runtime."
        if self.backend is None:
            return False, self.last_error or "Backend libusb1 introuvable."
        return True, "Backend libusb1 chargé."

    def enumerate(self) -> EnumerationResult:
        ok, detail = self.backend_status()
        if not ok:
            LOGGER.warning("Enumeration USB indisponible: %s", detail)
            return EnumerationResult(False, [], detail, {"backend_status": detail})

        devices: list[USBDevice] = []
        skipped_count = 0
        try:
            raw_devices = usb.core.find(find_all=True, backend=self.backend)
        except Exception as exc:  # pragma: no cover - hardware dependent
            self.last_error = str(exc)
            LOGGER.exception("Erreur pendant l'énumération USB.")
            return EnumerationResult(False, [], f"Erreur d'énumération USB: {exc}", {"backend_status": self.last_error})

        for raw_device in raw_devices or []:
            try:
                devices.append(self._build_device(raw_device))
            except Exception as exc:  # pragma: no cover - hardware dependent
                LOGGER.debug("Périphérique USB ignoré: %s", exc)
                skipped_count += 1
        return EnumerationResult(True, devices, "Snapshot USB collecté.", {"skipped_devices": skipped_count})

    def _resolve_backend(self):
        if libusb1 is None:
            return None

        dll_path = self._find_libusb_dll()
        try:
            if dll_path:
                return libusb1.get_backend(find_library=lambda _name: str(dll_path))
            return libusb1.get_backend()
        except Exception as exc:  # pragma: no cover - environment dependent
            self.last_error = str(exc)
            LOGGER.exception("Impossible de charger le backend libusb1.")
            return None

    def _find_libusb_dll(self) -> Path | None:
        candidates: list[Path] = []
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir:
            candidates.append(Path(bundle_dir) / "libusb-1.0.dll")

        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "libusb-1.0.dll")
        candidates.append(exe_dir / "_internal" / "libusb-1.0.dll")

        try:
            import libusb_package  # type: ignore

            module_dir = Path(libusb_package.__file__).resolve().parent
            candidates.append(module_dir / "libusb-1.0.dll")
        except ImportError:
            pass

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _build_device(self, raw_device) -> USBDevice:
        vendor_name = self._safe_get_string(raw_device, getattr(raw_device, "iManufacturer", None), "Inconnu")
        product_name = self._safe_get_string(raw_device, getattr(raw_device, "iProduct", None), "Périphérique USB")
        serial_number = self._safe_get_string(raw_device, getattr(raw_device, "iSerialNumber", None), None)
        interface_classes = self._extract_interface_classes(raw_device)
        usb_class = getattr(raw_device, "bDeviceClass", None)
        category, source, confidence = self.classifier.classify(
            usb_class,
            interface_classes,
            vendor_name,
            product_name,
        )
        bus = getattr(raw_device, "bus", None)
        address = getattr(raw_device, "address", None)
        device_key = self._build_device_key(raw_device.idVendor, raw_device.idProduct, serial_number, bus, address)
        return USBDevice(
            device_key=device_key,
            vid=getattr(raw_device, "idVendor", None),
            pid=getattr(raw_device, "idProduct", None),
            vendor_name=vendor_name or "Inconnu",
            product_name=product_name or "Périphérique USB",
            serial_number=serial_number,
            usb_class=usb_class,
            category=category,
            bus=bus,
            address=address,
            confidence=confidence,
            identification_source=source,
            source_backend="pyusb-libusb1",
            metadata={"interface_classes": interface_classes},
        )

    def _extract_interface_classes(self, raw_device) -> list[int]:
        classes: list[int] = []
        try:
            for configuration in raw_device:
                for interface in configuration:
                    class_code = getattr(interface, "bInterfaceClass", None)
                    if class_code is not None:
                        classes.append(int(class_code))
        except Exception:
            LOGGER.debug("Classes d'interface indisponibles pour un périphérique.")
        return classes

    def _safe_get_string(self, raw_device, index, fallback: str | None) -> str | None:
        if not index:
            return fallback
        try:
            value = usb.util.get_string(raw_device, index)
            return value or fallback
        except Exception:
            return fallback

    def _build_device_key(
        self,
        vid: int | None,
        pid: int | None,
        serial_number: str | None,
        bus: int | None,
        address: int | None,
    ) -> str:
        vid_text = "????" if vid is None else f"{vid:04X}"
        pid_text = "????" if pid is None else f"{pid:04X}"
        if serial_number:
            return f"{vid_text}:{pid_text}:{serial_number}"
        bus_value = "?" if bus is None else str(bus)
        address_value = "?" if address is None else str(address)
        return f"{vid_text}:{pid_text}:{bus_value}:{address_value}"
