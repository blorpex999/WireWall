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
DEVICE_INSTALL_RESTRICTIONS_PATH = r"SOFTWARE\Policies\Microsoft\Windows\DeviceInstall\Restrictions"
DENY_DEVICE_CLASSES_PATH = rf"{DEVICE_INSTALL_RESTRICTIONS_PATH}\DenyDeviceClasses"
DENY_DEVICE_IDS_PATH = rf"{DEVICE_INSTALL_RESTRICTIONS_PATH}\DenyDeviceIDs"
DENY_INSTANCE_IDS_PATH = rf"{DEVICE_INSTALL_RESTRICTIONS_PATH}\DenyInstanceIDs"
REMOVABLE_STORAGE_DEVICES_PATH = r"SOFTWARE\Policies\Microsoft\Windows\RemovableStorageDevices"
USB_LOCKDOWN_BACKUP_VALUE = "UsbPortLockdownServiceStarts"
USB_LOCKDOWN_PNP_BACKUP_VALUE = "UsbPortLockdownPnpInstanceIds"
USB_LOCKDOWN_POLICY_BACKUP_VALUE = "UsbPortLockdownPolicyBackup"


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

    def apply_usb_lockdown_policies(
        self,
        class_guids: list[str],
        device_ids: list[str] | None = None,
        instance_ids: list[str] | None = None,
    ) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        backup = self._read_policy_backup()
        classes = [str(guid).strip() for guid in class_guids if str(guid).strip()]
        devices = [str(device_id).strip() for device_id in (device_ids or []) if str(device_id).strip()]
        instances = [str(instance_id).strip() for instance_id in (instance_ids or []) if str(instance_id).strip()]
        try:
            self._write_policy_backup(backup)
            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, DEVICE_INSTALL_RESTRICTIONS_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "DenyDeviceClasses", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "DenyDeviceClassesRetroactive", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "DenyDeviceIDs", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "DenyDeviceIDsRetroactive", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "DenyInstanceIDs", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "DenyInstanceIDsRetroactive", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "DenyRemovableDevices", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "DenyRemovableDevicesRetroactive", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "AllowDenyLayered", 0, winreg.REG_DWORD, 1)
            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, DENY_DEVICE_CLASSES_PATH, 0, winreg.KEY_SET_VALUE) as key:
                for index, class_guid in enumerate(classes, start=1):
                    winreg.SetValueEx(key, str(index), 0, winreg.REG_SZ, class_guid)
            self._write_string_values(DENY_DEVICE_IDS_PATH, devices)
            self._write_string_values(DENY_INSTANCE_IDS_PATH, instances)
            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, REMOVABLE_STORAGE_DEVICES_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "Deny_All", 0, winreg.REG_DWORD, 1)
            return OperationResult(True, "applied", "Policies Windows USB appliquees.", {"classes": classes, "device_ids": devices, "instance_ids": instances})
        except PermissionError:
            return OperationResult(False, "permission_denied", "Privileges administrateur requis pour appliquer les policies USB.")
        except OSError as exc:
            return OperationResult(False, "error", f"Erreur policies USB: {exc}")

    def restore_usb_lockdown_policies(self) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        backup_result = self.load_usb_lockdown_policy_backup()
        backup = backup_result.details.get("backup", {}) if backup_result.success else {}
        try:
            self._restore_policy_dword(DEVICE_INSTALL_RESTRICTIONS_PATH, "DenyDeviceClasses", backup)
            self._restore_policy_dword(DEVICE_INSTALL_RESTRICTIONS_PATH, "DenyDeviceClassesRetroactive", backup)
            self._restore_policy_dword(DEVICE_INSTALL_RESTRICTIONS_PATH, "DenyDeviceIDs", backup)
            self._restore_policy_dword(DEVICE_INSTALL_RESTRICTIONS_PATH, "DenyDeviceIDsRetroactive", backup)
            self._restore_policy_dword(DEVICE_INSTALL_RESTRICTIONS_PATH, "DenyInstanceIDs", backup)
            self._restore_policy_dword(DEVICE_INSTALL_RESTRICTIONS_PATH, "DenyInstanceIDsRetroactive", backup)
            self._restore_policy_dword(DEVICE_INSTALL_RESTRICTIONS_PATH, "DenyRemovableDevices", backup)
            self._restore_policy_dword(DEVICE_INSTALL_RESTRICTIONS_PATH, "DenyRemovableDevicesRetroactive", backup)
            self._restore_policy_dword(DEVICE_INSTALL_RESTRICTIONS_PATH, "AllowDenyLayered", backup)
            self._restore_policy_dword(REMOVABLE_STORAGE_DEVICES_PATH, "Deny_All", backup)
            self._restore_string_value_key(DENY_DEVICE_CLASSES_PATH, backup, "deny_device_classes")
            self._restore_string_value_key(DENY_DEVICE_IDS_PATH, backup, "deny_device_ids")
            self._restore_string_value_key(DENY_INSTANCE_IDS_PATH, backup, "deny_instance_ids")
            return OperationResult(True, "restored", "Policies Windows USB restaurees.", {"backup_used": backup_result.success})
        except PermissionError:
            return OperationResult(False, "permission_denied", "Privileges administrateur requis pour restaurer les policies USB.")
        except OSError as exc:
            return OperationResult(False, "error", f"Erreur restauration policies USB: {exc}")

    def load_usb_lockdown_policy_backup(self) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le registre Windows n'est pas disponible.")
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WIREWALL_REG_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, USB_LOCKDOWN_POLICY_BACKUP_VALUE)
            parsed = json.loads(str(value))
            return OperationResult(True, "loaded", "Sauvegarde WireWall des policies USB chargee.", {"backup": parsed})
        except FileNotFoundError:
            return OperationResult(False, "not_found", "Aucune sauvegarde WireWall des policies USB.")
        except PermissionError:
            return OperationResult(False, "permission_denied", "Lecture de la sauvegarde policies WireWall refusee.")
        except (OSError, ValueError, TypeError) as exc:
            return OperationResult(False, "error", f"Sauvegarde policies WireWall illisible: {exc}")

    def _read_policy_backup(self) -> dict[str, object]:
        existing = self.load_usb_lockdown_policy_backup()
        if existing.success:
            return dict(existing.details.get("backup", {}))
        return {
            "dwords": {
                DEVICE_INSTALL_RESTRICTIONS_PATH: self._read_dwords(
                    DEVICE_INSTALL_RESTRICTIONS_PATH,
                    [
                        "DenyDeviceClasses",
                        "DenyDeviceClassesRetroactive",
                        "DenyDeviceIDs",
                        "DenyDeviceIDsRetroactive",
                        "DenyInstanceIDs",
                        "DenyInstanceIDsRetroactive",
                        "DenyRemovableDevices",
                        "DenyRemovableDevicesRetroactive",
                        "AllowDenyLayered",
                    ],
                ),
                REMOVABLE_STORAGE_DEVICES_PATH: self._read_dwords(REMOVABLE_STORAGE_DEVICES_PATH, ["Deny_All"]),
            },
            "deny_device_classes": self._read_string_values(DENY_DEVICE_CLASSES_PATH),
            "deny_device_ids": self._read_string_values(DENY_DEVICE_IDS_PATH),
            "deny_instance_ids": self._read_string_values(DENY_INSTANCE_IDS_PATH),
        }

    def _write_policy_backup(self, backup: dict[str, object]) -> None:
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, WIREWALL_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, USB_LOCKDOWN_POLICY_BACKUP_VALUE, 0, winreg.REG_SZ, json.dumps(backup, sort_keys=True))

    def _read_dwords(self, path: str, value_names: list[str]) -> dict[str, int | None]:
        values: dict[str, int | None] = {}
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ) as key:
                for value_name in value_names:
                    try:
                        value, _ = winreg.QueryValueEx(key, value_name)
                        values[value_name] = int(value)
                    except FileNotFoundError:
                        values[value_name] = None
        except FileNotFoundError:
            for value_name in value_names:
                values[value_name] = None
        return values

    def _read_string_values(self, path: str) -> dict[str, str]:
        values: dict[str, str] = {}
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ) as key:
                index = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    values[str(name)] = str(value)
                    index += 1
        except FileNotFoundError:
            pass
        return values

    def _write_string_values(self, path: str, values: list[str]) -> None:
        existing = self._read_string_values(path)
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE) as key:
            for value_name in existing:
                try:
                    winreg.DeleteValue(key, value_name)
                except FileNotFoundError:
                    pass
            for index, value in enumerate(values, start=1):
                winreg.SetValueEx(key, str(index), 0, winreg.REG_SZ, value)

    def _restore_policy_dword(self, path: str, value_name: str, backup: dict[str, object]) -> None:
        dwords = backup.get("dwords", {}) if isinstance(backup.get("dwords", {}), dict) else {}
        path_values = dwords.get(path, {}) if isinstance(dwords.get(path, {}), dict) else {}
        original = path_values.get(value_name)
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE) as key:
            if original is None:
                try:
                    winreg.DeleteValue(key, value_name)
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, int(original))

    def _restore_string_value_key(self, path: str, backup: dict[str, object], backup_key: str) -> None:
        try:
            winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, path)
        except FileNotFoundError:
            pass
        except OSError:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ) as key:
                for value_name in list(self._read_string_values(path)):
                    try:
                        winreg.DeleteValue(key, value_name)
                    except FileNotFoundError:
                        pass
        original_values = backup.get(backup_key, {})
        if isinstance(original_values, dict) and original_values:
            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE) as key:
                for name, value in original_values.items():
                    winreg.SetValueEx(key, str(name), 0, winreg.REG_SZ, str(value))

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
