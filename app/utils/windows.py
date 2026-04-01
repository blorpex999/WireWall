from __future__ import annotations

import ctypes
import logging
import os
import platform
import sys
from ctypes import wintypes
from typing import Callable

LOGGER = logging.getLogger(__name__)


class WindowsDeviceNotificationHook:
    WM_DEVICECHANGE = 0x0219
    DBT_DEVICEARRIVAL = 0x8000
    DBT_DEVICEREMOVECOMPLETE = 0x8004
    GWL_WNDPROC = -4

    def __init__(self) -> None:
        self._hwnd: int | None = None
        self._old_proc: int | None = None
        self._new_proc = None

    def attach(self, widget, callback: Callable[[str, int], None]) -> bool:
        if platform.system() != "Windows":
            return False

        hwnd = widget.winfo_id()
        user32 = ctypes.windll.user32
        is_64bit = ctypes.sizeof(ctypes.c_void_p) == ctypes.sizeof(ctypes.c_longlong)

        if is_64bit:
            set_window_long = user32.SetWindowLongPtrW
            call_window_proc = user32.CallWindowProcW
            set_window_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
        else:
            set_window_long = user32.SetWindowLongW
            call_window_proc = user32.CallWindowProcW
            set_window_long.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]

        WNDPROC = ctypes.WINFUNCTYPE(
            wintypes.LPARAM,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )
        set_window_long.restype = wintypes.LPARAM
        call_window_proc.restype = wintypes.LPARAM

        def _wnd_proc(hwnd_value, msg, wparam, lparam):
            if msg == self.WM_DEVICECHANGE and wparam in (
                self.DBT_DEVICEARRIVAL,
                self.DBT_DEVICEREMOVECOMPLETE,
            ):
                try:
                    callback("devicechange", int(wparam))
                except Exception:
                    LOGGER.exception("Erreur dans le callback WM_DEVICECHANGE.")
            return call_window_proc(self._old_proc, hwnd_value, msg, wparam, lparam)

        try:
            self._new_proc = WNDPROC(_wnd_proc)
            if is_64bit:
                proc_ptr = ctypes.cast(self._new_proc, ctypes.c_void_p)
                self._old_proc = int(set_window_long(hwnd, self.GWL_WNDPROC, proc_ptr))
            else:
                proc_ptr = ctypes.cast(self._new_proc, ctypes.c_void_p).value or 0
                self._old_proc = int(set_window_long(hwnd, self.GWL_WNDPROC, wintypes.LONG(proc_ptr)))
            self._hwnd = hwnd
            return True
        except Exception:
            LOGGER.exception("Impossible d'attacher le hook WM_DEVICECHANGE.")
            self._hwnd = None
            self._old_proc = None
            self._new_proc = None
            return False

    def detach(self) -> None:
        if self._hwnd is None or self._old_proc is None:
            return
        user32 = ctypes.windll.user32
        try:
            if ctypes.sizeof(ctypes.c_void_p) == ctypes.sizeof(ctypes.c_longlong):
                user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
                user32.SetWindowLongPtrW.restype = wintypes.LPARAM
                user32.SetWindowLongPtrW(self._hwnd, self.GWL_WNDPROC, ctypes.c_void_p(self._old_proc))
            else:
                user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
                user32.SetWindowLongW.restype = wintypes.LONG
                user32.SetWindowLongW(self._hwnd, self.GWL_WNDPROC, wintypes.LONG(self._old_proc))
        except Exception:
            LOGGER.exception("Impossible de detacher le hook WM_DEVICECHANGE.")
        finally:
            self._hwnd = None
            self._old_proc = None
            self._new_proc = None


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
