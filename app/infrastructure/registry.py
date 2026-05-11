from __future__ import annotations

import json
from dataclasses import dataclass

from app.models.entities import OperationResult

try:
    import winreg
except ImportError:  # pragma: no cover - Windows only
    winreg = None


USBSTOR_REG_PATH = r"SYSTEM\CurrentControlSet\Services\USBSTOR"
SERVICES_REG_ROOT = r"SYSTEM\CurrentControlSet\Services"
WIREWALL_REG_PATH = r"SOFTWARE\WireWall"
USB_LOCKDOWN_BACKUP_VALUE = "UsbPortLockdownServiceStarts"
USB_LOCKDOWN_PNP_BACKUP_VALUE = "UsbPortLockdownPnpInstanceIds"


@dataclass(slots=True)
class RegistryManager:
    def get_usbstor_start(self) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, USBSTOR_REG_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, "Start")
            status = "blocked" if value == 4 else "enabled" if value == 3 else "custom"
            return OperationResult(
                True,
                status,
                "Etat USBSTOR lu avec succès.",
                {"start_value": value, "registry_path": USBSTOR_REG_PATH},
            )
        except PermissionError:
            return OperationResult(False, "permission_denied", "Lecture USBSTOR refusée par le système.")
        except FileNotFoundError:
            return OperationResult(False, "not_found", "Clé USBSTOR introuvable.")
        except OSError as exc:
            return OperationResult(False, "error", f"Erreur registre: {exc}")

    def get_service_start(self, service_name: str) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        registry_path = rf"{SERVICES_REG_ROOT}\{service_name}"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, "Start")
            return OperationResult(True, "read", f"Etat du service {service_name} lu.", {"service": service_name, "start_value": value})
        except PermissionError:
            return OperationResult(False, "permission_denied", f"Lecture du service {service_name} refusee.")
        except FileNotFoundError:
            return OperationResult(False, "not_found", f"Service {service_name} introuvable.")
        except OSError as exc:
            return OperationResult(False, "error", f"Erreur registre {service_name}: {exc}")

    def set_service_start(self, service_name: str, value: int) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        registry_path = rf"{SERVICES_REG_ROOT}\{service_name}"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, int(value))
            verification = self.get_service_start(service_name)
            if not verification.success:
                return OperationResult(False, "verification_failed", verification.message, verification.details)
            if verification.details.get("start_value") != value:
                return OperationResult(False, "mismatch", f"La verification du service {service_name} a echoue.", verification.details)
            return OperationResult(True, "changed", f"Service {service_name} modifie.", {"service": service_name, "start_value": value})
        except PermissionError:
            return OperationResult(False, "permission_denied", f"Privileges administrateur requis pour modifier {service_name}.")
        except FileNotFoundError:
            return OperationResult(False, "not_found", f"Service {service_name} introuvable.")
        except OSError as exc:
            return OperationResult(False, "error", f"Erreur registre {service_name}: {exc}")

    def save_usb_lockdown_backup(self, values: dict[str, int]) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        try:
            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, WIREWALL_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, USB_LOCKDOWN_BACKUP_VALUE, 0, winreg.REG_SZ, json.dumps(values, sort_keys=True))
            return OperationResult(True, "saved", "Sauvegarde WireWall du verrouillage USB enregistree.", {"backup": values})
        except PermissionError:
            return OperationResult(False, "permission_denied", "Privileges administrateur requis pour sauvegarder l'etat USB.")
        except OSError as exc:
            return OperationResult(False, "error", f"Erreur sauvegarde WireWall: {exc}")

    def load_usb_lockdown_backup(self) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WIREWALL_REG_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, USB_LOCKDOWN_BACKUP_VALUE)
            parsed = json.loads(str(value))
            backup = {str(name): int(start_value) for name, start_value in parsed.items()}
            return OperationResult(True, "loaded", "Sauvegarde WireWall du verrouillage USB chargee.", {"backup": backup})
        except FileNotFoundError:
            return OperationResult(False, "not_found", "Aucune sauvegarde WireWall du verrouillage USB.")
        except PermissionError:
            return OperationResult(False, "permission_denied", "Lecture de la sauvegarde WireWall refusee.")
        except (OSError, ValueError, TypeError) as exc:
            return OperationResult(False, "error", f"Sauvegarde WireWall illisible: {exc}")

    def save_usb_lockdown_pnp_backup(self, instance_ids: list[str]) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        values = [str(instance_id) for instance_id in instance_ids if str(instance_id).strip()]
        try:
            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, WIREWALL_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, USB_LOCKDOWN_PNP_BACKUP_VALUE, 0, winreg.REG_SZ, json.dumps(values))
            return OperationResult(True, "saved", "Sauvegarde WireWall des peripheriques USB PnP enregistree.", {"instance_ids": values})
        except PermissionError:
            return OperationResult(False, "permission_denied", "Privileges administrateur requis pour sauvegarder les peripheriques USB.")
        except OSError as exc:
            return OperationResult(False, "error", f"Erreur sauvegarde PnP WireWall: {exc}")

    def load_usb_lockdown_pnp_backup(self) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WIREWALL_REG_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, USB_LOCKDOWN_PNP_BACKUP_VALUE)
            parsed = json.loads(str(value))
            instance_ids = [str(instance_id) for instance_id in parsed if str(instance_id).strip()]
            return OperationResult(True, "loaded", "Sauvegarde WireWall des peripheriques USB PnP chargee.", {"instance_ids": instance_ids})
        except FileNotFoundError:
            return OperationResult(False, "not_found", "Aucune sauvegarde WireWall des peripheriques USB PnP.")
        except PermissionError:
            return OperationResult(False, "permission_denied", "Lecture de la sauvegarde WireWall PnP refusee.")
        except (OSError, ValueError, TypeError) as exc:
            return OperationResult(False, "error", f"Sauvegarde WireWall PnP illisible: {exc}")

    def set_usbstor_start(self, value: int) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, USBSTOR_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, int(value))
            verification = self.get_usbstor_start()
            if not verification.success:
                return OperationResult(False, "verification_failed", verification.message)
            if verification.details.get("start_value") != value:
                return OperationResult(False, "mismatch", "La vérification post-écriture a échoué.", verification.details)
            state = "blocked" if value == 4 else "enabled" if value == 3 else "custom"
            details = dict(verification.details)
            details["requested_value"] = value
            return OperationResult(True, state, "Modification USBSTOR appliquée.", details)
        except PermissionError:
            return OperationResult(False, "permission_denied", "Privilèges administrateur requis pour modifier USBSTOR.")
        except FileNotFoundError:
            return OperationResult(False, "not_found", "Clé USBSTOR introuvable.")
        except OSError as exc:
            return OperationResult(False, "error", f"Erreur registre: {exc}")
