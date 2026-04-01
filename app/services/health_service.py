from __future__ import annotations

import os

from app.models.entities import HealthStatus
from app.utils.admin import is_admin
from app.utils.datetime import utc_now


class HealthCheckService:
    def __init__(self, db, paths, enumerator, usb_control_service, ollama_service, health_repo, exports_dir_getter) -> None:
        self.db = db
        self.paths = paths
        self.enumerator = enumerator
        self.usb_control_service = usb_control_service
        self.ollama_service = ollama_service
        self.health_repo = health_repo
        self.exports_dir_getter = exports_dir_getter

    def run_all(self, demo_mode: bool = False) -> list[HealthStatus]:
        statuses = [
            self._usb_backend_status(),
            self._db_status(),
            self._admin_status(),
            self._usbstor_status(),
            self.ollama_service.health_check(demo_mode=demo_mode),
            self._folder_status("logs", self.paths.logs_dir),
            self._folder_status("exports", self.exports_dir_getter()),
        ]
        self.health_repo.replace_all(statuses)
        return statuses

    def _usb_backend_status(self) -> HealthStatus:
        ok, detail = self.enumerator.backend_status()
        return HealthStatus("usb_backend", "ok" if ok else "warning", detail, utc_now())

    def _db_status(self) -> HealthStatus:
        try:
            healthy = self.db.healthcheck()
            return HealthStatus("database", "ok" if healthy else "error", "SQLite opérationnelle." if healthy else "Echec DB.", utc_now())
        except Exception as exc:
            return HealthStatus("database", "error", f"Erreur DB: {exc}", utc_now())

    def _admin_status(self) -> HealthStatus:
        return HealthStatus(
            "admin",
            "ok" if is_admin() else "warning",
            "Session administrateur active." if is_admin() else "Session non élevée. Les actions USBSTOR seront limitées.",
            utc_now(),
        )

    def _usbstor_status(self) -> HealthStatus:
        status = self.usb_control_service.get_status()
        level = "ok" if status.success else "warning"
        return HealthStatus("usbstor", level, f"{status.status}: {status.message}", utc_now())

    def _folder_status(self, name: str, path) -> HealthStatus:
        writable = os.access(path, os.W_OK) if path.exists() else False
        detail = f"{path} {'accessible' if writable else 'non accessible'}"
        return HealthStatus(name, "ok" if writable else "warning", detail, utc_now())
