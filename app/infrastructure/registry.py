from __future__ import annotations

from dataclasses import dataclass

from app.models.entities import OperationResult

try:
    import winreg
except ImportError:  # pragma: no cover - Windows only
    winreg = None


USBSTOR_REG_PATH = r"SYSTEM\CurrentControlSet\Services\USBSTOR"


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
