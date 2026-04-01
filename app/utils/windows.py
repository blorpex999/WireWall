from __future__ import annotations

import ctypes
import logging
import os
import platform
import sys
from contextlib import contextmanager
from ctypes import wintypes
from typing import Callable, Iterator

LOGGER = logging.getLogger(__name__)


WM_SETREDRAW = 0x000B
RDW_INVALIDATE = 0x0001
RDW_ERASE = 0x0004
RDW_ALLCHILDREN = 0x0080
RDW_FRAME = 0x0400


def _user32():
    return ctypes.windll.user32


def redraw_widget(widget) -> None:
    if platform.system() != "Windows":
        return
    try:
        hwnd = widget.winfo_id()
        user32 = _user32()
        user32.RedrawWindow.argtypes = [wintypes.HWND, ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]
        user32.RedrawWindow.restype = wintypes.BOOL
        user32.RedrawWindow(hwnd, None, None, RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN | RDW_FRAME)
    except Exception:
        LOGGER.exception("Impossible de forcer le redraw Win32 du widget.")


@contextmanager
def freeze_redraw(*widgets) -> Iterator[None]:
    if platform.system() != "Windows":
        yield
        return

    try:
        user32 = _user32()
        user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.SendMessageW.restype = wintypes.LPARAM
        user32.RedrawWindow.argtypes = [wintypes.HWND, ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]
        user32.RedrawWindow.restype = wintypes.BOOL
    except Exception:
        LOGGER.exception("Impossible d'initialiser les appels Win32 de redraw.")
        yield
        return

    hwnds: list[int] = []
    try:
        for widget in widgets:
            if widget is None:
                continue
            try:
                if not widget.winfo_exists():
                    continue
                hwnd = int(widget.winfo_id())
            except Exception:
                continue
            if hwnd in hwnds:
                continue
            user32.SendMessageW(hwnd, WM_SETREDRAW, 0, 0)
            hwnds.append(hwnd)
        yield
    finally:
        for hwnd in reversed(hwnds):
            try:
                user32.SendMessageW(hwnd, WM_SETREDRAW, 1, 0)
                user32.RedrawWindow(hwnd, None, None, RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN | RDW_FRAME)
            except Exception:
                LOGGER.exception("Impossible de retablir le redraw Win32.")


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
