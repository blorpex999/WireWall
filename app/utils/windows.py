from __future__ import annotations

import ctypes
import logging
import os
import platform
from ctypes import wintypes
from typing import Callable

from PyQt6.QtCore import QAbstractNativeEventFilter

LOGGER = logging.getLogger(__name__)


class WindowsDeviceNotificationFilter(QAbstractNativeEventFilter):
    WM_DEVICECHANGE = 0x0219
    DBT_DEVICEARRIVAL = 0x8000
    DBT_DEVICEREMOVECOMPLETE = 0x8004

    def __init__(self, callback: Callable[[str, int], None]) -> None:
        super().__init__()
        self._callback = callback

    def nativeEventFilter(self, event_type, message) -> tuple[bool, int]:
        if platform.system() != "Windows":
            return False, 0
        try:
            event_name = bytes(event_type).decode("ascii", errors="ignore")
            if event_name not in {"windows_generic_MSG", "windows_dispatcher_MSG"}:
                return False, 0
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == self.WM_DEVICECHANGE and int(msg.wParam) in {
                self.DBT_DEVICEARRIVAL,
                self.DBT_DEVICEREMOVECOMPLETE,
            }:
                self._callback("devicechange", int(msg.wParam))
        except Exception:
            LOGGER.exception("Erreur dans WindowsDeviceNotificationFilter.")
        return False, 0


def hide_console_window() -> None:
    if platform.system() != "Windows" or os.environ.get("WIREWALL_KEEP_CONSOLE") == "1":
        return

    try:
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
    except Exception:
        LOGGER.exception("Impossible de masquer la console Windows WireWall.")


def set_app_user_model_id(app_id: str = "WireWall.Desktop") -> None:
    if platform.system() != "Windows":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        LOGGER.exception("Impossible de definir l'AppUserModelID Windows de WireWall.")
