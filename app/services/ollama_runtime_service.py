from __future__ import annotations

import ctypes
import logging
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from app.models.entities import OperationResult


LOGGER = logging.getLogger(__name__)
DEFAULT_OLLAMA_PORT = 11434
LOCAL_OLLAMA_HOSTS = {"127.0.0.1", "localhost", "::1"}
PROCESS_TERMINATE = 0x0001
PROCESS_SET_QUOTA = 0x0100
PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION_STRUCT(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class OllamaRuntimeService:
    def __init__(self, base_url: str, model: str, startup_timeout_seconds: float = 3.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.startup_timeout_seconds = startup_timeout_seconds
        self._managed_process: subprocess.Popen[bytes] | None = None
        self._job_handle: int | None = None

    def update(self, *, base_url: str, model: str) -> OperationResult | None:
        previous_base_url = self.base_url
        self.base_url = base_url.rstrip("/")
        self.model = model
        if previous_base_url == self.base_url or self._managed_process is None:
            return None
        self.stop()
        return self.ensure_started()

    def ensure_started(self) -> OperationResult:
        managed_process = self._managed_process
        if managed_process is not None and managed_process.poll() is None:
            return OperationResult(
                True,
                "running",
                "Ollama local est deja gere par WireWall.",
                {"managed": True, "pid": managed_process.pid, "model": self.model},
            )

        if self._api_responds():
            self._managed_process = None
            self._close_job_handle()
            return OperationResult(
                True,
                "running",
                f"Ollama local est deja actif pour le modele configure '{self.model}'.",
                {"managed": False, "model": self.model, "base_url": self.base_url},
            )

        host = self._resolve_local_host()
        if host is None:
            return OperationResult(
                False,
                "unsupported",
                "Le demarrage automatique d'Ollama n'est supporte que pour une URL locale.",
                {"base_url": self.base_url},
            )

        executable = shutil.which("ollama")
        if executable is None:
            return OperationResult(
                False,
                "missing",
                "Ollama n'est pas installe sur ce poste.",
                {"base_url": self.base_url, "model": self.model},
            )

        env = os.environ.copy()
        env["OLLAMA_HOST"] = host
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0

        try:
            process = subprocess.Popen(
                [executable, "serve"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                creationflags=creationflags,
                close_fds=True,
            )
        except OSError as exc:
            LOGGER.warning("Demarrage automatique d'Ollama impossible: %s", exc)
            return OperationResult(
                False,
                "start_failed",
                f"Impossible de lancer Ollama automatiquement: {exc}",
                {"base_url": self.base_url, "model": self.model, "executable": executable},
            )

        self._managed_process = process
        self._bind_managed_process_to_job(process.pid)
        if self._wait_until_ready():
            LOGGER.info("Ollama demarre automatiquement pour WireWall (pid=%s).", process.pid)
            return OperationResult(
                True,
                "started",
                f"Ollama local a ete lance automatiquement pour le modele configure '{self.model}'.",
                {"managed": True, "pid": process.pid, "base_url": self.base_url, "model": self.model},
            )

        if process.poll() is not None:
            exit_code = process.returncode
            self._managed_process = None
            self._close_job_handle()
            LOGGER.warning("Le processus Ollama demarre par WireWall s'est termine trop tot (code=%s).", exit_code)
            return OperationResult(
                False,
                "start_failed",
                "Ollama a ete lance par WireWall, mais le processus s'est arrete avant de repondre.",
                {"managed": True, "exit_code": exit_code, "base_url": self.base_url, "model": self.model},
            )

        LOGGER.info("Ollama a ete lance par WireWall et termine encore son demarrage.")
        return OperationResult(
            True,
            "starting",
            "Ollama a ete lance par WireWall et termine encore son demarrage.",
            {"managed": True, "pid": process.pid, "base_url": self.base_url, "model": self.model},
        )

    def stop(self) -> OperationResult:
        process = self._managed_process
        if process is None:
            self._close_job_handle()
            return OperationResult(True, "not_managed", "Aucun processus Ollama gere par WireWall a arreter.", {})

        self._managed_process = None
        if process.poll() is not None:
            self._close_job_handle()
            return OperationResult(
                True,
                "stopped",
                "Le processus Ollama gere par WireWall etait deja arrete.",
                {"pid": process.pid, "exit_code": process.returncode},
            )

        try:
            process.terminate()
            process.wait(timeout=5)
            self._close_job_handle()
            LOGGER.info("Processus Ollama gere par WireWall arrete (pid=%s).", process.pid)
            return OperationResult(True, "stopped", "Ollama lance par WireWall a ete arrete.", {"pid": process.pid})
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
            self._close_job_handle()
            LOGGER.warning("Processus Ollama gere par WireWall tue apres timeout (pid=%s).", process.pid)
            return OperationResult(
                True,
                "killed",
                "Ollama lance par WireWall ne repondait plus et a ete force a s'arreter.",
                {"pid": process.pid},
            )
        except OSError as exc:
            self._close_job_handle()
            LOGGER.warning("Arret du processus Ollama gere par WireWall impossible: %s", exc)
            return OperationResult(False, "stop_failed", f"Impossible d'arreter Ollama: {exc}", {"pid": process.pid})

    def _resolve_local_host(self) -> str | None:
        parsed = urlparse(self.base_url)
        scheme = parsed.scheme.lower()
        hostname = (parsed.hostname or "").lower()
        if scheme not in {"", "http"}:
            return None
        if hostname not in LOCAL_OLLAMA_HOSTS:
            return None
        port = parsed.port or DEFAULT_OLLAMA_PORT
        return f"{hostname}:{port}"

    def _wait_until_ready(self) -> bool:
        deadline = time.monotonic() + max(0.0, self.startup_timeout_seconds)
        while time.monotonic() < deadline:
            if self._api_responds():
                return True
            process = self._managed_process
            if process is not None and process.poll() is not None:
                return False
            time.sleep(0.2)
        return self._api_responds()

    def _api_responds(self) -> bool:
        try:
            with urlopen(f"{self.base_url}/api/tags", timeout=1.5) as response:
                return 200 <= getattr(response, "status", 200) < 300
        except (HTTPError, URLError, ValueError, TimeoutError, OSError):
            return False

    def _bind_managed_process_to_job(self, pid: int) -> None:
        if sys.platform != "win32":
            return

        self._close_job_handle()
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            LOGGER.warning("Impossible de creer le job Windows pour Ollama (pid=%s).", pid)
            return

        process_handle = None
        try:
            limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION_STRUCT()
            limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not kernel32.SetInformationJobObject(
                job,
                JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                ctypes.byref(limits),
                ctypes.sizeof(limits),
            ):
                LOGGER.warning("Impossible d'activer le kill-on-close sur le job Ollama (pid=%s).", pid)
                return

            process_handle = kernel32.OpenProcess(
                PROCESS_TERMINATE | PROCESS_SET_QUOTA | PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                pid,
            )
            if not process_handle:
                LOGGER.warning("Impossible d'ouvrir le process Ollama pour l'attacher au job Windows (pid=%s).", pid)
                return

            if not kernel32.AssignProcessToJobObject(job, process_handle):
                LOGGER.warning("Impossible d'attacher Ollama au job Windows (pid=%s).", pid)
                return

            self._job_handle = int(job)
            job = None
        finally:
            if process_handle:
                kernel32.CloseHandle(process_handle)
            if job:
                kernel32.CloseHandle(job)

    def _close_job_handle(self) -> None:
        if self._job_handle is None or sys.platform != "win32":
            self._job_handle = None
            return

        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL
            kernel32.CloseHandle(wintypes.HANDLE(self._job_handle))
        except Exception:
            LOGGER.exception("Impossible de fermer le job Windows associe a Ollama.")
        finally:
            self._job_handle = None
