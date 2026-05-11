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
        component_statuses = [
            self._usb_backend_status(),
            self._db_status(),
            self._admin_status(),
            self._usbstor_status(),
            self.ollama_service.health_check(demo_mode=demo_mode),
            self._folder_status("logs", self.paths.logs_dir),
            self._folder_status("exports", self.exports_dir_getter()),
        ]
        statuses = [
            *component_statuses,
            self._degraded_mode_status(component_statuses, demo_mode),
            self._reliability_status(component_statuses, demo_mode),
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

    def _degraded_mode_status(self, statuses: list[HealthStatus], demo_mode: bool) -> HealthStatus:
        degraded_parts: list[str] = []
        status_map = {status.component: status for status in statuses}
        if status_map.get("usb_backend") and status_map["usb_backend"].status != "ok":
            degraded_parts.append("monitoring USB limite")
        if status_map.get("usbstor") and status_map["usbstor"].status != "ok":
            degraded_parts.append("controle USBSTOR en lecture/indisponible")
        if status_map.get("ollama") and status_map["ollama"].status != "ok":
            degraded_parts.append("analyse IA locale desactivee")
        if status_map.get("admin") and status_map["admin"].status != "ok":
            degraded_parts.append("actions administrateur limitees")
        if demo_mode:
            degraded_parts.append("actions reelles suspendues par le mode demo")

        if not degraded_parts:
            return HealthStatus("degraded_mode", "ok", "Tous les modules critiques sont disponibles.", utc_now())
        return HealthStatus(
            "degraded_mode",
            "warning",
            "Mode degrade actif: " + ", ".join(degraded_parts) + ".",
            utc_now(),
        )

    def _reliability_status(self, statuses: list[HealthStatus], demo_mode: bool) -> HealthStatus:
        errors = [status.component for status in statuses if status.status == "error"]
        warnings = [status.component for status in statuses if status.status == "warning"]
        if errors:
            return HealthStatus(
                "reliability",
                "error",
                "Diagnostic bloquant: " + ", ".join(errors) + ".",
                utc_now(),
            )
        if warnings:
            return HealthStatus(
                "reliability",
                "warning",
                "Fiabilite degradee mais application exploitable: " + ", ".join(warnings) + ".",
                utc_now(),
            )
        mode = "demo" if demo_mode else "reel"
        return HealthStatus("reliability", "ok", f"Diagnostic de demarrage OK en mode {mode}.", utc_now())
