from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Any

from app.config.defaults import PROFILE_PRESETS
from app.models.entities import AIAnalysis, AppSettings, HealthStatus
from app.utils.admin import relaunch_as_admin
from app.utils.datetime import hours_ago, utc_now


class AppController:
    def __init__(self, container) -> None:
        self.container = container

    @property
    def settings(self) -> AppSettings:
        return self.container.settings

    @property
    def demo_mode(self) -> bool:
        return self.settings.mode == "demo"

    def start_services(self) -> None:
        self.container.usb_monitor.start()

    def stop_services(self) -> None:
        self.container.usb_monitor.stop()

    def refresh_monitor(self) -> None:
        self.container.usb_monitor.refresh_now()

    def run_health_checks(self):
        return self.request_health_refresh()

    def request_health_refresh(self) -> bool:
        return self.container.background_tasks.submit_unique(
            "health_refresh",
            self.container.health_service.run_all,
            success_event="health_refresh_completed",
            error_event="background_task_error",
        )

    def get_dashboard_data(self) -> dict[str, Any]:
        devices = self.container.device_repo.list_all(demo_mode=self.demo_mode)
        alerts = self.container.alert_repo.list_all(demo_mode=self.demo_mode)
        events = self.container.event_repo.list_recent(limit=15, demo_mode=self.demo_mode)
        health = self.container.health_repo.list_all()
        counts = self.container.device_repo.counts(self.demo_mode)
        alert_counts = self.container.alert_repo.counts(self.demo_mode)
        usb_status = self.container.usb_control_service.get_status()
        ollama_status = self.get_ollama_health_status()
        global_score = int(mean([device.risk_score for device in devices])) if devices else 0
        return {
            "global_score": global_score,
            "device_count": len(devices),
            "connected_count": counts.get("connected", 0),
            "events_today": self.container.event_repo.count_today(self.demo_mode, hours_ago(24)),
            "alerts_total": len(alerts),
            "critical_alerts": alert_counts.get("CRITICAL", 0),
            "recent_events": events,
            "top_alerts": alerts[:8],
            "health": health,
            "usb_status": usb_status,
            "ollama_status": ollama_status,
        }

    def list_devices(self, search: str = "", category: str = "", status: str = ""):
        return self.container.device_repo.list_all(search=search, category=category, status=status, demo_mode=self.demo_mode)

    def get_device(self, device_key: str):
        return self.container.device_repo.get(device_key)

    def whitelist_device(self, device_key: str) -> None:
        device = self._require_device(device_key)
        value = device.serial_number if device.serial_number else device.vid_pid
        match_type = "serial" if device.serial_number else "vid_pid"
        self.container.policy_service.add_entry(
            policy_type="whitelist",
            match_type=match_type,
            value=value,
            label=device.display_name,
            notes="Ajouté depuis l'interface Devices",
        )

    def blacklist_device(self, device_key: str) -> None:
        device = self._require_device(device_key)
        value = device.serial_number if device.serial_number else device.vid_pid
        match_type = "serial" if device.serial_number else "vid_pid"
        self.container.policy_service.add_entry(
            policy_type="blacklist",
            match_type=match_type,
            value=value,
            label=device.display_name,
            notes="Ajouté depuis l'interface Devices",
        )

    def list_alerts(self, severity: str = "", acknowledged: str = ""):
        return self.container.alert_repo.list_all(severity=severity, acknowledged=acknowledged, demo_mode=self.demo_mode)

    def acknowledge_alert(self, alert_id: int) -> None:
        self.container.alert_repo.acknowledge(alert_id, utc_now())

    def list_events(self, search: str = "", severity: str = ""):
        return self.container.event_repo.list_recent(search=search, severity=severity, demo_mode=self.demo_mode)

    def list_policies(self, policy_type: str = "", query: str = ""):
        return self.container.policy_service.list_entries(policy_type=policy_type, query=query)

    def add_policy(self, policy_type: str, match_type: str, value: str, label: str, notes: str) -> None:
        self.container.policy_service.add_entry(
            policy_type=policy_type,
            match_type=match_type,
            value=value,
            label=label,
            notes=notes,
        )

    def remove_policy(self, entry_id: int) -> None:
        self.container.policy_service.remove_entry(entry_id)

    def import_policies(self, path: str) -> int:
        return self.container.policy_service.import_entries(Path(path))

    def export_policies(self, path: str) -> Path:
        return self.container.policy_service.export_entries(Path(path))

    def get_usb_control_status(self):
        return self.container.usb_control_service.get_status()

    def block_usb_storage(self):
        return self.container.usb_control_service.block_storage()

    def unblock_usb_storage(self):
        return self.container.usb_control_service.unblock_storage()

    def relaunch_admin(self) -> bool:
        return relaunch_as_admin()

    def usb_diagnostics(self) -> dict[str, object]:
        return self.container.usb_control_service.diagnostics()

    def request_ai_analysis(self) -> bool:
        return self.container.background_tasks.submit_unique(
            "ai_analysis",
            self._run_ai_analysis_sync,
            success_event="ai_analysis_completed",
            error_event="background_task_error",
        )

    def list_ai_analyses(self):
        return self.container.ai_analysis_repo.list_recent()

    def export_report(self, fmt: str) -> Path:
        if fmt == "html":
            return self.container.report_service.export_html(self.demo_mode)
        if fmt == "json":
            return self.container.report_service.export_json(self.demo_mode)
        if fmt == "csv":
            return self.container.report_service.export_csv(self.demo_mode)
        raise ValueError("Format d'export non supporté.")

    def get_health_statuses(self):
        return self.container.health_repo.list_all()

    def get_ollama_health_status(self) -> HealthStatus:
        return self.container.health_repo.get("ollama") or HealthStatus(
            component="ollama",
            status="unknown",
            details="Aucun health check Ollama disponible.",
            checked_at=utc_now(),
        )

    def get_database_path(self) -> Path:
        return self.container.db.db_path

    def is_task_running(self, name: str) -> bool:
        return self.container.background_tasks.is_running(name)

    def save_settings(self, values: dict[str, str]) -> AppSettings:
        settings_payload = self.settings.to_dict()
        scan_interval = self._parse_positive_int(values["scan_interval_seconds"], "Fréquence de scan")
        retention_days = self._parse_positive_int(values["history_retention_days"], "Rétention historique")
        ollama_timeout = self._parse_positive_int(values["ollama_timeout_seconds"], "Timeout Ollama")
        export_directory = values["export_directory"].strip() or str(self.container.paths.exports_dir)
        settings_payload.update(
            {
                "scan_interval_seconds": scan_interval,
                "history_retention_days": retention_days,
                "log_level": values["log_level"],
                "ollama_base_url": values["ollama_base_url"],
                "ollama_model": values["ollama_model"],
                "ollama_timeout_seconds": ollama_timeout,
                "security_profile": values["security_profile"],
                "export_directory": export_directory,
            }
        )
        preset = PROFILE_PRESETS.get(values["security_profile"], {})
        settings_payload["alert_threshold"] = int(preset.get("alert_threshold", settings_payload["alert_threshold"]))
        settings_payload["dedup_window_seconds"] = int(
            preset.get("dedup_window_seconds", settings_payload["dedup_window_seconds"])
        )
        settings = AppSettings(**settings_payload)
        self.container.settings = settings
        self.container.settings_repo.save(settings)
        self.container.config_loader.save(settings)
        self.container.report_service.exports_dir = Path(settings.export_directory)
        self.container.report_service.exports_dir.mkdir(parents=True, exist_ok=True)
        self.container.ollama_service.update(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
        self.container.usb_monitor.update_settings(settings)
        self.container.retention_service.apply(settings.history_retention_days)
        self.request_health_refresh()
        return settings

    def _run_ai_analysis_sync(self) -> AIAnalysis:
        context = self.container.report_service.build_context(self.demo_mode)
        analysis = self.container.ollama_service.analyze(context)
        self.container.ai_analysis_repo.add(analysis)
        return analysis

    def _parse_positive_int(self, raw_value: str, label: str) -> int:
        try:
            value = int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{label}: valeur entière invalide.") from exc
        if value <= 0:
            raise ValueError(f"{label}: la valeur doit être strictement positive.")
        return value

    def _require_device(self, device_key: str):
        device = self.container.device_repo.get(device_key)
        if device is None:
            raise ValueError("Périphérique introuvable.")
        return device
