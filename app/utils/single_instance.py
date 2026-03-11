from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)

ERROR_ALREADY_EXISTS = 183
SW_RESTORE = 9
SW_SHOW = 5


@dataclass(slots=True)
class SingleInstanceGuard:
    handle: int | None
    already_running: bool
    existing_window_activated: bool

    def release(self) -> None:
        if self.handle is None or sys.platform != "win32":
            self.handle = None
            return

        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL
            kernel32.CloseHandle(wintypes.HANDLE(self.handle))
        except Exception:
            LOGGER.exception("Impossible de liberer le mutex d'instance unique.")
        finally:
            self.handle = None


def acquire_single_instance(app_name: str = "WireWall") -> SingleInstanceGuard:
    if sys.platform != "win32":
        return SingleInstanceGuard(handle=None, already_running=False, existing_window_activated=False)

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE

    mutex_name = f"Local\\{app_name}-SingleInstance"
    ctypes.set_last_error(0)
    handle = kernel32.CreateMutexW(None, False, mutex_name)
    if not handle:
        error_code = ctypes.get_last_error()
        raise OSError(error_code, "Impossible de creer le verrou d'instance unique WireWall.")

    already_running = ctypes.get_last_error() == ERROR_ALREADY_EXISTS
    activated = False
    if already_running:
        activated = activate_existing_window(app_name)

    return SingleInstanceGuard(
        handle=int(handle),
        already_running=already_running,
        existing_window_activated=activated,
    )


def activate_existing_window(window_title_prefix: str = "WireWall") -> bool:
    if sys.platform != "win32":
        return False

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.BringWindowToTop.restype = wintypes.BOOL

    found_hwnd: dict[str, int] = {"hwnd": 0}

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum_windows(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True

        title_length = user32.GetWindowTextLengthW(hwnd)
        if title_length <= 0:
            return True

        title_buffer = ctypes.create_unicode_buffer(title_length + 1)
        user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
        title = title_buffer.value.strip()
        if not title.startswith(window_title_prefix):
            return True

        found_hwnd["hwnd"] = int(hwnd)
        return False

    try:
        user32.EnumWindows(_enum_windows, 0)
        hwnd = found_hwnd["hwnd"]
        if not hwnd:
            return False

        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        else:
            user32.ShowWindow(hwnd, SW_SHOW)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        LOGGER.exception("Impossible d'activer la fenetre WireWall deja ouverte.")
        return False
