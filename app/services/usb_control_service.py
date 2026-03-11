from __future__ import annotations

from app.infrastructure.registry import RegistryManager
from app.models.entities import OperationResult
from app.utils.admin import is_admin


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

    def diagnostics(self) -> dict[str, object]:
        registry_status = self.get_status()
        return {
            "is_admin": is_admin(),
            "registry_status": registry_status.status,
            "registry_message": registry_status.message,
            "registry_details": registry_status.details,
        }
