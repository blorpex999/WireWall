from __future__ import annotations

from app.infrastructure.registry import RegistryManager
from app.models.entities import OperationResult
from app.utils.admin import is_admin

USB_LOCKDOWN_SERVICES = {
    "USBXHCI": 3,
    "USBHUB3": 3,
    "usbhub": 3,
    "UCX01000": 3,
}


class UsbControlService:
    def __init__(self, registry_manager: RegistryManager) -> None:
        self.registry_manager = registry_manager

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
                "note": (
                    "Ce controle agit sur les services Windows de controle/hub USB. "
                    "Il peut couper souris, clavier, hubs, disques et autres peripheriques USB, souvent apres redemarrage."
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
                {"results": results, "failures": failures, "backup": current, "missing": missing},
            )
        return OperationResult(
            True,
            "blocked",
            "Verrouillage total USB applique. Un redemarrage peut etre necessaire.",
            {
                "action": "block_all_usb",
                "results": results,
                "backup": current,
                "missing": missing,
                "warning": "Les souris, claviers et hubs USB peuvent cesser de fonctionner.",
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
        results = {}
        failures = {}
        for service_name, start_value in target_values.items():
            result = self.registry_manager.set_service_start(service_name, int(start_value))
            results[service_name] = result.status
            if not result.success:
                failures[service_name] = result.message
        if failures:
            return OperationResult(
                False,
                "partial",
                "Restauration USB partiellement appliquee.",
                {"results": results, "failures": failures, "backup_used": backup.success},
            )
        return OperationResult(
            True,
            "enabled",
            "Ports USB restaures. Un redemarrage peut etre necessaire.",
            {"action": "restore_all_usb", "results": results, "backup_used": backup.success},
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
