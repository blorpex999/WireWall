from __future__ import annotations

from app.infrastructure.pnp_devices import PnpDeviceManager
from app.infrastructure.registry import RegistryManager
from app.models.entities import OperationResult
from app.utils.admin import is_admin

USB_LOCKDOWN_SERVICES = {
    "USBXHCI": 3,
    "USBHUB3": 3,
    "usbhub": 3,
    "UCX01000": 3,
}

USB_LOCKDOWN_CLASS_GUIDS = [
    "{36fc9e60-c465-11cf-8056-444553540000}",  # USB host controllers and hubs
    "{88bae032-5a81-49f0-bc3d-a4ff138216d6}",  # USBDevice
    "{745a17a0-74d3-11d0-b6fe-00a0c90f57da}",  # HIDClass
    "{4d36e96b-e325-11ce-bfc1-08002be10318}",  # Keyboard
    "{4d36e96f-e325-11ce-bfc1-08002be10318}",  # Mouse
    "{4d36e967-e325-11ce-bfc1-08002be10318}",  # DiskDrive
    "{4d36e97b-e325-11ce-bfc1-08002be10318}",  # SCSIAdapter / UASP storage
    "{eec5ad98-8080-425f-922a-dabf3de3f69a}",  # WPD portable devices
]


class UsbControlService:
    def __init__(self, registry_manager: RegistryManager, pnp_device_manager: PnpDeviceManager | None = None) -> None:
        self.registry_manager = registry_manager
        self.pnp_device_manager = pnp_device_manager or PnpDeviceManager()

    def get_status(self) -> OperationResult:
        status = self.registry_manager.get_usbstor_start()
        status.details["is_admin"] = is_admin()
        return status

    def block_storage(self) -> OperationResult:
        if not is_admin():
            return OperationResult(
                False,
                "permission_denied",
                "Le blocage USB storage requiert une session administrateur.",
                {"is_admin": False},
            )
        result = self.registry_manager.set_usbstor_start(4)
        result.details["action"] = "block"
        result.details["note"] = (
            "Le blocage agit sur USBSTOR. Un périphérique déjà monté peut nécessiter une réinsertion ou une nouvelle session."
        )
        return result

    def unblock_storage(self) -> OperationResult:
        if not is_admin():
            return OperationResult(
                False,
                "permission_denied",
                "Le déblocage USB storage requiert une session administrateur.",
                {"is_admin": False},
            )
        result = self.registry_manager.set_usbstor_start(3)
        result.details["action"] = "unblock"
        result.details["note"] = (
            "Le déblocage agit sur USBSTOR. Un périphérique déjà présent peut nécessiter une réinsertion pour être repris."
        )
        return result

    def get_full_lockdown_status(self) -> OperationResult:
        service_states = {}
        errors = {}
        for service_name in USB_LOCKDOWN_SERVICES:
            result = self.registry_manager.get_service_start(service_name)
            if result.success:
                service_states[service_name] = int(result.details.get("start_value", -1))
            elif result.status != "not_found":
                errors[service_name] = result.status
        if not service_states:
            return OperationResult(
                False,
                "not_available",
                "Aucun service Windows de controle USB total n'a pu etre lu.",
                {"is_admin": is_admin(), "errors": errors},
            )
        blocked = [name for name, value in service_states.items() if value == 4]
        if len(blocked) == len(service_states):
            status = "blocked"
            message = "Verrouillage USB total actif sur les services detectes."
        elif blocked:
            status = "partial"
            message = "Verrouillage USB total partiel: certains services USB sont bloques."
        else:
            status = "enabled"
            message = "Ports USB systeme autorises."
        backup = self.registry_manager.load_usb_lockdown_backup()
        policy_backup = self.registry_manager.load_usb_lockdown_policy_backup()
        return OperationResult(
            True,
            status,
            message,
            {
                "is_admin": is_admin(),
                "services": service_states,
                "blocked_services": blocked,
                "errors": errors,
                "backup_available": backup.success,
                "backup": backup.details.get("backup", {}) if backup.success else {},
                "policy_backup_available": policy_backup.success,
                "note": (
                    "Ce controle applique les policies Windows officielles, bloque les services USB et desactive les peripheriques PnP presents. "
                    "Il peut couper souris, clavier, hubs, disques et autres peripheriques USB; un redemarrage peut renforcer l'effet."
                ),
            },
        )

    def block_all_usb_ports(self) -> OperationResult:
        if not is_admin():
            return OperationResult(
                False,
                "permission_denied",
                "Le verrouillage total USB requiert une session administrateur.",
                {"is_admin": False},
            )
        current = {}
        missing = []
        for service_name in USB_LOCKDOWN_SERVICES:
            state = self.registry_manager.get_service_start(service_name)
            if state.success:
                current[service_name] = int(state.details.get("start_value", USB_LOCKDOWN_SERVICES[service_name]))
            elif state.status == "not_found":
                missing.append(service_name)
            else:
                return OperationResult(False, state.status, state.message, {"service": service_name})
        backup_result = self.registry_manager.save_usb_lockdown_backup(current)
        if not backup_result.success:
            return backup_result

        pnp_candidates = self.pnp_device_manager.list_lockdown_candidates()
        pnp_devices = pnp_candidates.details.get("devices", []) if pnp_candidates.success else []
        pnp_instance_ids = [str(device["instance_id"]) for device in pnp_devices if device.get("instance_id")]
        pnp_backup = self.registry_manager.save_usb_lockdown_pnp_backup(pnp_instance_ids)
        if not pnp_backup.success:
            return pnp_backup
        policy_result = self.registry_manager.apply_usb_lockdown_policies(USB_LOCKDOWN_CLASS_GUIDS)
        if not policy_result.success:
            return policy_result
        policy_refresh = self.pnp_device_manager.apply_policy_refresh()

        results = {}
        failures = {}
        for service_name in current:
            result = self.registry_manager.set_service_start(service_name, 4)
            results[service_name] = result.status
            if not result.success:
                failures[service_name] = result.message
        if failures:
            return OperationResult(
                False,
                "partial",
                "Verrouillage total USB partiellement applique.",
                {"results": results, "failures": failures, "backup": current, "missing": missing, "pnp_candidates": pnp_devices},
            )
        class_disable = self.pnp_device_manager.disable_usb_device_ids()
        pnp_disable = self.pnp_device_manager.disable_devices(pnp_instance_ids)
        pnp_details = pnp_disable.details if pnp_disable.details else {}
        if pnp_candidates.success and not pnp_disable.success:
            return OperationResult(
                False,
                "partial",
                "Policies/services USB appliques, mais certains peripheriques deja branches n'ont pas pu etre desactives.",
                {
                    "results": results,
                    "backup": current,
                    "missing": missing,
                    "policy_result": policy_result.details,
                    "policy_refresh": policy_refresh.details,
                    "class_disable": class_disable.details,
                    "pnp_candidates": pnp_devices,
                    "pnp_result": pnp_details,
                },
            )
        return OperationResult(
            True,
            "blocked",
            "Verrouillage USB renforce applique: policies Windows, services et peripheriques presents traites.",
            {
                "action": "block_all_usb",
                "results": results,
                "backup": current,
                "missing": missing,
                "policy_result": policy_result.details,
                "policy_refresh": policy_refresh.details,
                "class_disable": class_disable.details,
                "pnp_candidates": pnp_devices,
                "pnp_result": pnp_details,
                "warning": "Les souris, claviers et hubs USB peuvent cesser de fonctionner immediatement.",
            },
        )

    def restore_all_usb_ports(self) -> OperationResult:
        if not is_admin():
            return OperationResult(
                False,
                "permission_denied",
                "La restauration USB totale requiert une session administrateur.",
                {"is_admin": False},
            )
        backup = self.registry_manager.load_usb_lockdown_backup()
        target_values = backup.details.get("backup", {}) if backup.success else dict(USB_LOCKDOWN_SERVICES)
        if target_values and all(int(value) == 4 for value in target_values.values()):
            target_values = dict(USB_LOCKDOWN_SERVICES)
        policy_restore = self.registry_manager.restore_usb_lockdown_policies()
        policy_refresh = self.pnp_device_manager.apply_policy_refresh()
        results = {}
        failures = {}
        for service_name, start_value in target_values.items():
            result = self.registry_manager.set_service_start(service_name, int(start_value))
            results[service_name] = result.status
            if not result.success:
                failures[service_name] = result.message
        pnp_backup = self.registry_manager.load_usb_lockdown_pnp_backup()
        pnp_instance_ids = pnp_backup.details.get("instance_ids", []) if pnp_backup.success else []
        pnp_restore = self.pnp_device_manager.enable_devices(pnp_instance_ids)
        if failures:
            return OperationResult(
                False,
                "partial",
                "Restauration USB partiellement appliquee.",
                {
                    "results": results,
                    "failures": failures,
                    "backup_used": backup.success,
                    "policy_restore": policy_restore.details,
                    "policy_refresh": policy_refresh.details,
                    "pnp_backup_used": pnp_backup.success,
                    "pnp_result": pnp_restore.details,
                },
            )
        if pnp_backup.success and not pnp_restore.success:
            return OperationResult(
                False,
                "partial",
                "Services USB restaures, mais certains peripheriques PnP n'ont pas pu etre reactives.",
                {
                    "results": results,
                    "backup_used": backup.success,
                    "policy_restore": policy_restore.details,
                    "policy_refresh": policy_refresh.details,
                    "pnp_backup_used": True,
                    "pnp_result": pnp_restore.details,
                },
            )
        return OperationResult(
            True,
            "enabled",
            "Ports USB restaures et peripheriques PnP reactives. Un redemarrage peut rester necessaire.",
            {
                "action": "restore_all_usb",
                "results": results,
                "backup_used": backup.success,
                "policy_restore": policy_restore.details,
                "policy_refresh": policy_refresh.details,
                "pnp_backup_used": pnp_backup.success,
                "pnp_result": pnp_restore.details,
            },
        )

    def diagnostics(self) -> dict[str, object]:
        registry_status = self.get_status()
        full_lockdown_status = self.get_full_lockdown_status()
        return {
            "is_admin": is_admin(),
            "registry_status": registry_status.status,
            "registry_message": registry_status.message,
            "registry_details": registry_status.details,
            "full_lockdown_status": full_lockdown_status.status,
            "full_lockdown_message": full_lockdown_status.message,
            "full_lockdown_details": full_lockdown_status.details,
        }
