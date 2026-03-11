from __future__ import annotations

import ctypes
import logging
import platform
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

        if ctypes.sizeof(ctypes.c_void_p) == ctypes.sizeof(ctypes.c_longlong):
            set_window_long = user32.SetWindowLongPtrW
            call_window_proc = user32.CallWindowProcW
        else:
            set_window_long = user32.SetWindowLongW
            call_window_proc = user32.CallWindowProcW

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
            self._old_proc = set_window_long(hwnd, self.GWL_WNDPROC, self._new_proc)
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
                user32.SetWindowLongPtrW(self._hwnd, self.GWL_WNDPROC, self._old_proc)
            else:
                user32.SetWindowLongW(self._hwnd, self.GWL_WNDPROC, self._old_proc)
        except Exception:
            LOGGER.exception("Impossible de détacher le hook WM_DEVICECHANGE.")
        finally:
            self._hwnd = None
            self._old_proc = None
            self._new_proc = None
