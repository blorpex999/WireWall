from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.models.entities import OperationResult

try:
    import winreg
except ImportError:  # pragma: no cover - Windows only
    winreg = None


AUTOSTART_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "WireWall"


class AutostartService:
    def get_status(self) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le demarrage automatique n'est disponible que sous Windows.")
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, AUTOSTART_NAME)
            return OperationResult(True, "enabled", "Demarrage automatique actif.", {"command": value})
        except FileNotFoundError:
            return OperationResult(True, "disabled", "Demarrage automatique desactive.", {})
        except OSError as exc:
            return OperationResult(False, "error", f"Lecture du demarrage automatique impossible: {exc}", {})

    def enable(self) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le demarrage automatique n'est disponible que sous Windows.")
        command = self._build_command()
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH) as key:
                winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, command)
            return OperationResult(True, "enabled", "Demarrage automatique active.", {"command": command})
        except OSError as exc:
            return OperationResult(False, "error", f"Activation du demarrage automatique impossible: {exc}", {"command": command})

    def disable(self) -> OperationResult:
        if winreg is None:
            return OperationResult(False, "unsupported", "Le demarrage automatique n'est disponible que sous Windows.")
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, AUTOSTART_NAME)
            return OperationResult(True, "disabled", "Demarrage automatique desactive.", {})
        except FileNotFoundError:
            return OperationResult(True, "disabled", "Demarrage automatique deja desactive.", {})
        except OSError as exc:
            return OperationResult(False, "error", f"Desactivation du demarrage automatique impossible: {exc}", {})

    def apply(self, enabled: bool) -> OperationResult:
        return self.enable() if enabled else self.disable()

    def _build_command(self) -> str:
        if getattr(sys, "frozen", False):
            return subprocess.list2cmdline([str(Path(sys.executable).resolve())])

        interpreter = Path(sys.executable).resolve()
        pythonw = interpreter.with_name("pythonw.exe")
        launcher = pythonw if pythonw.exists() else interpreter
        script_path = Path(sys.argv[0]).resolve()
        return subprocess.list2cmdline([str(launcher), str(script_path)])
