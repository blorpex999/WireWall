from __future__ import annotations

from app.core.constants import USB_CLASS_MAP

GENERIC_VENDOR_NAMES = {"", "inconnu", "unknown", "manufacturer"}
GENERIC_PRODUCT_NAMES = {"", "peripherique usb", "pÃ©riphÃ©rique usb", "pÃƒÂ©riphÃƒÂ©rique usb", "usb device", "unknown"}

VID_VENDOR_HINTS = {
    0x05AC: "Apple",
    0x046D: "Logitech",
    0x0781: "SanDisk",
    0x0951: "Kingston",
    0x0BDA: "Realtek",
    0x0C45: "Sonix Technology",
    0x0E0F: "VMware",
    0x1058: "Western Digital",
    0x13FE: "Phison",
    0x174C: "ASMedia",
    0x1A40: "Terminus Technology",
    0x1A86: "QinHeng Electronics",
    0x2109: "VIA Labs",
    0x413C: "Dell",
    0x8087: "Intel",
}

CATEGORY_KIND = {
    "storage": "support de stockage USB",
    "hid": "peripherique de saisie HID",
    "hub": "hub USB",
    "imaging": "camera ou capteur video USB",
    "communication": "peripherique de communication USB",
    "audio_video": "peripherique audio/video USB",
    "vendor_specific": "peripherique specifique constructeur",
    "unknown": "peripherique USB non identifie",
}

CLASS_HINTS = {
    0x01: "classe audio",
    0x02: "classe communication",
    0x03: "classe HID",
    0x06: "classe imagerie",
    0x08: "classe stockage",
    0x09: "classe hub",
    0x0A: "classe donnees CDC",
    0x0E: "classe video",
    0xE0: "classe sans fil",
    0xFF: "classe constructeur",
}


class DeviceClassifier:
    def classify(
        self,
        usb_class: int | None,
        interface_classes: list[int] | None,
        vendor_name: str,
        product_name: str,
    ) -> tuple[str, str, float]:
        name_blob = f"{vendor_name} {product_name}".lower()
        if any(token in name_blob for token in ("iphone", "ipad", "ipod", "apple mobile device")):
            return "communication", "product_hint", 0.72

        if usb_class in USB_CLASS_MAP:
            return USB_CLASS_MAP[usb_class], "usb_class", 0.9

        if interface_classes:
            for class_code in interface_classes:
                if class_code in USB_CLASS_MAP:
                    return USB_CLASS_MAP[class_code], "interface_class", 0.75

        if any(token in name_blob for token in ("storage", "disk", "flash", "mass")):
            return "storage", "product_hint", 0.6
        if any(token in name_blob for token in ("keyboard", "mouse", "hid")):
            return "hid", "product_hint", 0.6
        if "hub" in name_blob:
            return "hub", "product_hint", 0.6
        if any(token in name_blob for token in ("camera", "image", "webcam")):
            return "imaging", "product_hint", 0.55
        if any(token in name_blob for token in ("audio", "microphone", "speaker", "headset", "sonix")):
            return "audio_video", "product_hint", 0.55
        if any(token in name_blob for token in ("modem", "serial", "com")):
            return "communication", "product_hint", 0.55

        return "unknown", "fallback", 0.35

    def enrich_identity(
        self,
        *,
        vid: int | None,
        pid: int | None,
        usb_class: int | None,
        interface_classes: list[int],
        vendor_name: str,
        product_name: str,
        category: str,
        source: str,
    ) -> dict[str, object]:
        raw_vendor = (vendor_name or "").strip()
        raw_product = (product_name or "").strip()
        vendor = self._best_vendor_name(vid, raw_vendor)
        kind = CATEGORY_KIND.get(category, CATEGORY_KIND["unknown"])
        product = self._best_product_name(vid, pid, vendor, raw_product, category, usb_class, interface_classes)
        friendly_name = self._friendly_name(vendor, product, kind)
        hints = self._identity_hints(vid, pid, usb_class, interface_classes, raw_vendor, raw_product, category, source)
        description = self._description(vendor, product, kind, category, hints)
        confidence_boost = 0.08 if vendor != raw_vendor or product != raw_product else 0.0
        return {
            "vendor_name": vendor,
            "product_name": product,
            "friendly_name": friendly_name,
            "description": description,
            "device_kind": kind,
            "identity_hints": hints,
            "raw_vendor_name": raw_vendor,
            "raw_product_name": raw_product,
            "confidence_boost": confidence_boost,
        }

    def _best_vendor_name(self, vid: int | None, raw_vendor: str) -> str:
        if raw_vendor and raw_vendor.lower() not in GENERIC_VENDOR_NAMES:
            if raw_vendor.lower() == "sonix":
                return "Sonix Technology"
            return raw_vendor
        if vid in VID_VENDOR_HINTS:
            return VID_VENDOR_HINTS[vid]
        return raw_vendor or "Inconnu"

    def _best_product_name(
        self,
        vid: int | None,
        pid: int | None,
        vendor: str,
        raw_product: str,
        category: str,
        usb_class: int | None,
        interface_classes: list[int],
    ) -> str:
        normalized = raw_product.strip().lower()
        if normalized and normalized not in GENERIC_PRODUCT_NAMES:
            return raw_product
        if vid == 0x05AC:
            if pid == 0x12A8:
                return "iPhone / iPad (Apple Mobile Device)"
            return "Appareil Apple USB"
        if "sonix" in vendor.lower() and (category in {"imaging", "audio_video"} or 0x0E in interface_classes):
            return "Camera ou capteur video USB"
        if category == "storage":
            return "Support de stockage USB"
        if category == "hid":
            return "Clavier, souris ou receiver HID"
        if category == "hub":
            return "Hub USB"
        if category == "imaging":
            return "Camera ou peripherique d'imagerie"
        if category == "audio_video":
            return "Peripherique audio/video"
        if category == "communication":
            return "Interface de communication USB"
        if usb_class == 0xFF:
            return "Peripherique specifique constructeur"
        return raw_product or "Peripherique USB"

    def _friendly_name(self, vendor: str, product: str, kind: str) -> str:
        if vendor and vendor.lower() not in GENERIC_VENDOR_NAMES:
            if product and vendor.lower() not in product.lower():
                return f"{vendor} - {product}"
            return product or vendor
        return product or kind.capitalize()

    def _identity_hints(
        self,
        vid: int | None,
        pid: int | None,
        usb_class: int | None,
        interface_classes: list[int],
        raw_vendor: str,
        raw_product: str,
        category: str,
        source: str,
    ) -> list[str]:
        hints = [f"VID:PID {self._vid_pid_text(vid, pid)}", f"Categorie {category}", f"Source {source}"]
        if usb_class in CLASS_HINTS:
            hints.append(CLASS_HINTS[usb_class])
        for class_code in sorted(set(interface_classes)):
            if class_code in CLASS_HINTS:
                hints.append(f"Interface {CLASS_HINTS[class_code]}")
        if raw_vendor:
            hints.append(f"Constructeur brut: {raw_vendor}")
        if raw_product:
            hints.append(f"Produit brut: {raw_product}")
        return hints

    def _description(self, vendor: str, product: str, kind: str, category: str, hints: list[str]) -> str:
        product_blob = product.lower()
        if "apple" in vendor.lower() and any(token in product_blob for token in ("iphone", "ipad", "ipod", "apple mobile")):
            return (
                "Appareil iOS detecte en USB. Il peut exposer plusieurs interfaces Windows "
                "(photos, synchronisation, pilotes Apple Mobile Device), donc WireWall le regroupe sous un nom lisible."
            )
        if "sonix" in vendor.lower() and category in {"imaging", "audio_video"}:
            return (
                "Controleur Sonix souvent utilise par des webcams, capteurs video ou modules audio USB. "
                "Verifier dans le Gestionnaire de peripheriques si cela correspond a une camera ou un micro attendu."
            )
        if category == "storage":
            return "Support de stockage USB: cle, disque externe ou lecteur de cartes. A traiter avec prudence s'il est nouveau."
        if category == "hid":
            return "Peripherique HID: clavier, souris, receiver ou interface de saisie. Un HID inconnu peut meriter verification."
        if category == "hub":
            return "Hub USB: composant qui expose plusieurs ports ou un hub interne du PC."
        if category == "imaging":
            return "Peripherique d'imagerie: webcam, camera ou scanner expose via USB."
        if category == "audio_video":
            return "Peripherique audio/video: micro, casque, webcam audio ou module multimedia USB."
        if category == "communication":
            return "Interface de communication: adaptateur serie, modem, bluetooth, reseau ou composant CDC."
        if category == "vendor_specific":
            return "Classe constructeur specifique: l'usage exact depend du pilote et du fabricant."
        return f"{kind.capitalize()}. Indices disponibles: {', '.join(hints[:3])}."

    def _vid_pid_text(self, vid: int | None, pid: int | None) -> str:
        vid_text = "????" if vid is None else f"{vid:04X}"
        pid_text = "????" if pid is None else f"{pid:04X}"
        return f"{vid_text}:{pid_text}"
