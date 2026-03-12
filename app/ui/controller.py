from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Any

from app.config.defaults import PROFILE_PRESETS
from app.models.entities import AIAnalysis, AppSettings, HealthStatus
from app.utils.admin import relaunch_as_admin
from app.utils.datetime import days_ago, hours_ago, parse_timestamp, utc_now


class AppController:
    def __init__(self, container) -> None:
        self.container = container
        self._last_settings_notice: tuple[str, str] | None = None

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

    def request_brain_refresh(self) -> bool:
        return self.container.background_tasks.submit_unique(
            "brain_refresh",
            lambda: self.container.brain_service.refresh(self.demo_mode, self.settings.recommendation_mode),
            success_event="brain_refresh_completed",
            error_event="background_task_error",
        )

    def get_dashboard_data(self) -> dict[str, Any]:
        devices = self.container.device_repo.list_all(demo_mode=self.demo_mode)
        alerts = self.container.alert_repo.list_all(demo_mode=self.demo_mode)
        incidents = self.container.incident_service.list_open(self.demo_mode)
        suggestions = self.container.recommendation_service.list_pending(self.demo_mode, limit=8)
        events = self.container.event_repo.list_recent(limit=15, demo_mode=self.demo_mode)
        health = self.container.health_repo.list_all()
        brain_snapshot = self.container.brain_service.latest(self.demo_mode)
        counts = self.container.device_repo.counts(self.demo_mode)
        alert_counts = self.container.alert_repo.counts(self.demo_mode)
        usb_status = self.container.usb_control_service.get_status()
        ollama_status = self.get_ollama_health_status()
        global_score = int(mean([device.risk_score for device in devices])) if devices else 0
        new_device_cutoff = parse_timestamp(days_ago(7))
        new_devices_7d = len(
            [
                device
                for device in devices
                if new_device_cutoff is not None
                and parse_timestamp(device.first_seen) is not None
                and parse_timestamp(device.first_seen) >= new_device_cutoff
            ]
        )
        deviation_count = len([device for device in devices if device.trust_state == "DEVIATION"])
        known_count = len([device for device in devices if device.trust_state == "KNOWN"])
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
            "brain_snapshot": brain_snapshot,
            "incidents": incidents[:8],
            "suggestions": suggestions,
            "open_incidents": len(incidents),
            "new_devices_7d": new_devices_7d,
            "deviation_count": deviation_count,
            "known_count": known_count,
        }

    def list_devices(self, search: str = "", category: str = "", status: str = ""):
        return self.container.device_repo.list_all(search=search, category=category, status=status, demo_mode=self.demo_mode)

    def get_device(self, device_key: str):
        return self.container.device_repo.get(device_key)

    def get_device_history(self, device_key: str, limit: int = 10):
        return self.container.event_repo.list_for_device(device_key, limit=limit, demo_mode=self.demo_mode)

    def whitelist_device(self, device_key: str) -> None:
        device = self._require_device(device_key)
        value = device.serial_number if device.serial_number else device.vid_pid
        match_type = "serial" if device.serial_number else "vid_pid"
        self.container.policy_service.add_entry(
            policy_type="whitelist",
            match_type=match_type,
            value=value,
            label=device.display_name,
            notes="Ajoute depuis l'interface Peripheriques",
        )
        self.container.device_repo.update_decision(device_key, "whitelist")
        self.request_brain_refresh()

    def blacklist_device(self, device_key: str) -> None:
        device = self._require_device(device_key)
        value = device.serial_number if device.serial_number else device.vid_pid
        match_type = "serial" if device.serial_number else "vid_pid"
        self.container.policy_service.add_entry(
            policy_type="blacklist",
            match_type=match_type,
            value=value,
            label=device.display_name,
            notes="Ajoute depuis l'interface Peripheriques",
        )
        self.container.device_repo.update_decision(device_key, "blacklist")
        self.request_brain_refresh()

    def list_alerts(self, severity: str = "", acknowledged: str = ""):
        return self.container.alert_repo.list_all(severity=severity, acknowledged=acknowledged, demo_mode=self.demo_mode)

    def acknowledge_alert(self, alert_id: int) -> None:
        self.container.alert_repo.acknowledge(alert_id, utc_now())
        self.request_brain_refresh()

    def get_alert_case(self, alert_id: int):
        return self.container.incident_service.get_by_alert(alert_id)

    def ensure_alert_case(self, alert_id: int):
        case = self.container.incident_service.ensure_for_alert(alert_id, self.demo_mode)
        self.request_brain_refresh()
        return case

    def update_alert_case(
        self,
        *,
        alert_id: int,
        status: str,
        decision: str,
        comment: str,
        resolution_reason: str,
    ):
        case = self.container.incident_service.update_case(
            alert_id=alert_id,
            demo_mode=self.demo_mode,
            status=status,
            decision=decision,
            comment=comment,
            resolution_reason=resolution_reason,
        )
        self.request_brain_refresh()
        return case

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
        self.request_brain_refresh()

    def remove_policy(self, entry_id: int) -> None:
        self.container.policy_service.remove_entry(entry_id)
        self.request_brain_refresh()

    def import_policies(self, path: str) -> int:
        count = self.container.policy_service.import_entries(Path(path))
        self.request_brain_refresh()
        return count

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
        raise ValueError("Format d'export non supporte.")

    def get_health_statuses(self):
        return self.container.health_repo.list_all()

    def get_ollama_health_status(self) -> HealthStatus:
        return self.container.health_repo.get("ollama") or HealthStatus(
            component="ollama",
            status="unknown",
            details="Aucun health check Ollama disponible.",
            checked_at=utc_now(),
        )

    def get_demo_precheck(self) -> list[dict[str, str]]:
        health_map = {status.component: status for status in self.get_health_statuses()}
        ollama_status = self.get_ollama_health_status()
        configured_model = self.settings.ollama_model

        rows = [
            self._build_precheck_row(
                key="mode",
                label="Mode courant",
                raw_status="warning" if self.demo_mode else "ok",
                detail="Mode demo isole." if self.demo_mode else "Mode reel actif.",
                action="Dire clairement au jury si la base de demonstration est active.",
            ),
            self._build_health_precheck(
                key="usb_backend",
                label="Backend USB",
                health_status=health_map.get("usb_backend"),
                blocking_on=("warning", "error"),
                fallback_action="Verifier libusb1 avant la demonstration.",
            ),
            self._build_health_precheck(
                key="database",
                label="Base SQLite",
                health_status=health_map.get("database"),
                blocking_on=("error",),
                fallback_action="Verifier les droits d'ecriture et l'integrite de la base locale.",
            ),
            self._build_health_precheck(
                key="logs",
                label="Dossier logs",
                health_status=health_map.get("logs"),
                fallback_action="Verifier l'acces a %LOCALAPPDATA%\\WireWall\\logs.",
            ),
            self._build_health_precheck(
                key="exports",
                label="Dossier exports",
                health_status=health_map.get("exports"),
                fallback_action="Choisir un dossier d'export accessible avant la demo.",
            ),
            self._build_health_precheck(
                key="admin",
                label="Session admin",
                health_status=health_map.get("admin"),
                fallback_action="Lancer WireWall en admin seulement si tu montres USBSTOR.",
            ),
            self._build_health_precheck(
                key="usbstor",
                label="Lecture USBSTOR",
                health_status=health_map.get("usbstor"),
                fallback_action="Verifier la cle USBSTOR ou basculer la demo sur le monitoring.",
            ),
        ]

        rows.append(
            self._build_precheck_row(
                key="ollama",
                label="Service Ollama",
                raw_status="ok" if ollama_status.status == "ok" else "warning",
                detail=ollama_status.details,
                action=(
                    "Ollama pret pour la demo IA."
                    if ollama_status.status == "ok"
                    else "La demo reste faisable sans IA; eviter cet ecran ou lancer l'assistant IA locale."
                ),
            )
        )
        rows.append(
            self._build_precheck_row(
                key="model",
                label="Modele IA attendu",
                raw_status="ok" if ollama_status.status == "ok" else "warning",
                detail=(
                    f"Modele configure '{configured_model}' present."
                    if ollama_status.status == "ok"
                    else f"Modele attendu '{configured_model}' non confirme."
                ),
                action="Si le modele manque, changer de modele dans Parametres ou ignorer la partie IA.",
            )
        )
        return rows

    def list_suggestions(self, limit: int = 12):
        return self.container.recommendation_service.list_pending(self.demo_mode, limit=limit)

    def accept_suggestion(self, recommendation_id: int):
        result = self.container.recommendation_service.accept(recommendation_id)
        self.request_brain_refresh()
        return result

    def reject_suggestion(self, recommendation_id: int, comment: str = ""):
        result = self.container.recommendation_service.reject(recommendation_id, comment)
        self.request_brain_refresh()
        return result

    def defer_suggestion(self, recommendation_id: int, comment: str = ""):
        result = self.container.recommendation_service.defer(recommendation_id, comment)
        self.request_brain_refresh()
        return result

    def get_autostart_status(self):
        return self.container.autostart_service.get_status()

    def apply_autostart(self, enabled: bool):
        return self.container.autostart_service.apply(enabled)

    def get_database_path(self) -> Path:
        return self.container.db.db_path

    def is_task_running(self, name: str) -> bool:
        return self.container.background_tasks.is_running(name)

    def consume_settings_notice(self) -> tuple[str, str] | None:
        notice = self._last_settings_notice
        self._last_settings_notice = None
        return notice

    def save_settings(self, values: dict[str, Any]) -> AppSettings:
        settings_payload = self.settings.to_dict()
        scan_interval = self._parse_positive_int(values["scan_interval_seconds"], "Frequence de scan")
        retention_days = self._parse_positive_int(values["history_retention_days"], "Retention historique")
        ollama_timeout = self._parse_positive_int(values["ollama_timeout_seconds"], "Timeout Ollama")
        export_directory = str(values["export_directory"]).strip() or str(self.container.paths.exports_dir)
        autostart_enabled = self._parse_bool(values.get("autostart_enabled", False))
        desktop_notifications_enabled = self._parse_bool(values.get("desktop_notifications_enabled", True))
        recommendation_mode = str(values.get("recommendation_mode", "balanced")).strip().lower() or "balanced"
        if recommendation_mode not in {"conservative", "balanced", "proactive"}:
            raise ValueError("Mode de recommandation invalide.")

        settings_payload.update(
            {
                "scan_interval_seconds": scan_interval,
                "history_retention_days": retention_days,
                "log_level": str(values["log_level"]),
                "ollama_base_url": str(values["ollama_base_url"]).strip(),
                "ollama_model": str(values["ollama_model"]).strip(),
                "ollama_timeout_seconds": ollama_timeout,
                "security_profile": str(values["security_profile"]),
                "export_directory": export_directory,
                "autostart_enabled": autostart_enabled,
                "desktop_notifications_enabled": desktop_notifications_enabled,
                "recommendation_mode": recommendation_mode,
            }
        )
        preset = PROFILE_PRESETS.get(settings_payload["security_profile"], {})
        settings_payload["alert_threshold"] = int(preset.get("alert_threshold", settings_payload["alert_threshold"]))
        settings_payload["dedup_window_seconds"] = int(
            preset.get("dedup_window_seconds", settings_payload["dedup_window_seconds"])
        )
        settings = AppSettings(**settings_payload)

        self._last_settings_notice = None
        if settings.mode != "demo":
            autostart_result = self.container.autostart_service.apply(settings.autostart_enabled)
            if not autostart_result.success:
                self._last_settings_notice = (autostart_result.message, "WARNING")
        else:
            self._last_settings_notice = ("Le demarrage automatique reste ignore en mode demo.", "INFO")

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
        self.request_brain_refresh()
        return settings

    def _run_ai_analysis_sync(self) -> AIAnalysis:
        self.container.brain_service.refresh(self.demo_mode, self.settings.recommendation_mode)
        context = self.container.report_service.build_ai_context(self.demo_mode)
        analysis = self.container.ollama_service.analyze(context)
        self.container.ai_analysis_repo.add(analysis)
        return analysis

    def _parse_positive_int(self, raw_value: str, label: str) -> int:
        try:
            value = int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{label}: valeur entiere invalide.") from exc
        if value <= 0:
            raise ValueError(f"{label}: la valeur doit etre strictement positive.")
        return value

    def _parse_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on", "oui"}

    def _require_device(self, device_key: str):
        device = self.container.device_repo.get(device_key)
        if device is None:
            raise ValueError("Peripherique introuvable.")
        return device

    def _build_health_precheck(
        self,
        *,
        key: str,
        label: str,
        health_status: HealthStatus | None,
        fallback_action: str,
        blocking_on: tuple[str, ...] = (),
    ) -> dict[str, str]:
        if health_status is None:
            return self._build_precheck_row(
                key=key,
                label=label,
                raw_status="warning",
                detail="Aucun controle disponible pour ce composant.",
                action=fallback_action,
            )
        raw_status = "error" if health_status.status in blocking_on else health_status.status
        return self._build_precheck_row(
            key=key,
            label=label,
            raw_status=raw_status,
            detail=health_status.details,
            action="Aucune action requise." if raw_status == "ok" else fallback_action,
        )

    def _build_precheck_row(
        self,
        *,
        key: str,
        label: str,
        raw_status: str,
        detail: str,
        action: str,
    ) -> dict[str, str]:
        normalized = raw_status.lower().strip()
        if normalized == "ok":
            tone = "OK"
            status = "OK"
        elif normalized == "error":
            tone = "ERROR"
            status = "Bloquant demo"
        else:
            tone = "WARNING"
            status = "A surveiller"
        return {
            "key": key,
            "label": label,
            "status": status,
            "tone": tone,
            "detail": detail,
            "action": action,
        }
