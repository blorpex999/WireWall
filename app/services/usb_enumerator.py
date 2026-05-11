from __future__ import annotations

import json
import logging
import re
import subprocess
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

        pnp_hints = self._windows_pnp_hints()
        for raw_device in raw_devices or []:
            try:
                devices.append(self._build_device(raw_device, pnp_hints))
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

    def _build_device(self, raw_device, pnp_hints: dict[tuple[int, int], list[dict[str, str]]] | None = None) -> USBDevice:
        vendor_name = self._safe_get_string(raw_device, getattr(raw_device, "iManufacturer", None), "Inconnu")
        product_name = self._safe_get_string(raw_device, getattr(raw_device, "iProduct", None), "Périphérique USB")
        serial_number = self._safe_get_string(raw_device, getattr(raw_device, "iSerialNumber", None), None)
        pnp_hint = self._match_windows_pnp_hint(
            pnp_hints or {},
            getattr(raw_device, "idVendor", None),
            getattr(raw_device, "idProduct", None),
            serial_number,
        )
        if pnp_hint and self._should_use_pnp_name(product_name, pnp_hint["friendly_name"]):
            product_name = pnp_hint["friendly_name"]
        interface_classes = self._extract_interface_classes(raw_device)
        usb_class = getattr(raw_device, "bDeviceClass", None)
        category, source, confidence = self.classifier.classify(
            usb_class,
            interface_classes,
            vendor_name,
            product_name,
        )
        identity = self.classifier.enrich_identity(
            vid=getattr(raw_device, "idVendor", None),
            pid=getattr(raw_device, "idProduct", None),
            usb_class=usb_class,
            interface_classes=interface_classes,
            vendor_name=vendor_name or "",
            product_name=product_name or "",
            category=category,
            source=source,
        )
        bus = getattr(raw_device, "bus", None)
        address = getattr(raw_device, "address", None)
        device_key = self._build_device_key(raw_device.idVendor, raw_device.idProduct, serial_number, bus, address)
        metadata = {
            "interface_classes": interface_classes,
            "friendly_name": identity["friendly_name"],
            "description": identity["description"],
            "device_kind": identity["device_kind"],
            "identity_hints": identity["identity_hints"],
            "raw_vendor_name": identity["raw_vendor_name"],
            "raw_product_name": identity["raw_product_name"],
        }
        if pnp_hint:
            metadata["windows_pnp_friendly_name"] = pnp_hint["friendly_name"]
            metadata["windows_pnp_class"] = pnp_hint["pnp_class"]
            metadata["windows_pnp_instance_id"] = pnp_hint["instance_id"]
        return USBDevice(
            device_key=device_key,
            vid=getattr(raw_device, "idVendor", None),
            pid=getattr(raw_device, "idProduct", None),
            vendor_name=str(identity["vendor_name"]),
            product_name=str(identity["product_name"]),
            serial_number=serial_number,
            usb_class=usb_class,
            category=category,
            bus=bus,
            address=address,
            confidence=min(0.95, confidence + float(identity["confidence_boost"])),
            identification_source=source,
            source_backend="pyusb-libusb1",
            metadata=metadata,
        )

    def _windows_pnp_hints(self) -> dict[tuple[int, int], list[dict[str, str]]]:
        if sys.platform != "win32":
            return {}
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            (
                "Get-PnpDevice -PresentOnly | "
                "Where-Object { $_.InstanceId -match '^USB\\\\VID_' } | "
                "Select-Object FriendlyName,InstanceId,Class | ConvertTo-Json -Compress"
            ),
        ]
        startupinfo = None
        creationflags = 0
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=2.5,
                check=False,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        except Exception:
            LOGGER.debug("Indices Windows PnP indisponibles.", exc_info=True)
            return {}
        if completed.returncode != 0 or not completed.stdout.strip():
            return {}
        try:
            parsed = json.loads(completed.stdout)
        except json.JSONDecodeError:
            LOGGER.debug("Reponse Windows PnP illisible: %s", completed.stdout[:200])
            return {}

        rows = parsed if isinstance(parsed, list) else [parsed]
        hints: dict[tuple[int, int], list[dict[str, str]]] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            instance_id = str(row.get("InstanceId") or "")
            match = re.search(r"VID_([0-9A-Fa-f]{4})&PID_([0-9A-Fa-f]{4})", instance_id)
            if not match:
                continue
            friendly_name = str(row.get("FriendlyName") or "").strip()
            if not friendly_name:
                continue
            key = (int(match.group(1), 16), int(match.group(2), 16))
            hints.setdefault(key, []).append(
                {
                    "friendly_name": friendly_name,
                    "instance_id": instance_id,
                    "pnp_class": str(row.get("Class") or ""),
                }
            )
        return hints

    def _match_windows_pnp_hint(
        self,
        pnp_hints: dict[tuple[int, int], list[dict[str, str]]],
        vid: int | None,
        pid: int | None,
        serial_number: str | None,
    ) -> dict[str, str] | None:
        if vid is None or pid is None:
            return None
        candidates = pnp_hints.get((vid, pid), [])
        if not candidates:
            return None
        serial = (serial_number or "").lower()

        def score(candidate: dict[str, str]) -> tuple[int, int]:
            name = candidate["friendly_name"].lower()
            instance_id = candidate["instance_id"].lower()
            value = 0
            if serial and serial in instance_id:
                value += 8
            if any(token in name for token in ("iphone", "ipad", "ipod")):
                value += 25
            if "apple mobile device" in name:
                value += 10
            if "composite" in name:
                value -= 2
            if name in {"usb device", "peripherique usb"}:
                value -= 5
            return value, len(name)

        return max(candidates, key=score)

    def _should_use_pnp_name(self, product_name: str | None, pnp_name: str) -> bool:
        product = (product_name or "").strip().lower()
        pnp = pnp_name.strip().lower()
        if not pnp:
            return False
        if product in {"", "usb device", "peripherique usb", "unknown"}:
            return True
        if any(token in pnp for token in ("iphone", "ipad", "ipod", "apple mobile device")):
            return True
        return product in pnp

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
