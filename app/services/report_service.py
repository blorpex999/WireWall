from __future__ import annotations

import csv
import hashlib
import html
import json
from pathlib import Path
from statistics import mean

from app.models.entities import Alert, DeviceEvent, HealthStatus, PolicyEntry, ReportAudit, USBDevice
from app.utils.datetime import utc_now


class ReportService:
    def __init__(
        self,
        exports_dir: Path,
        device_repo,
        event_repo,
        policy_service,
        alert_repo,
        health_repo,
        ai_analysis_repo,
        brain_snapshot_repo,
        incident_service=None,
        recommendation_service=None,
        report_audit_repo=None,
        settings_getter=None,
    ) -> None:
        self.exports_dir = exports_dir
        self.device_repo = device_repo
        self.event_repo = event_repo
        self.policy_service = policy_service
        self.alert_repo = alert_repo
        self.health_repo = health_repo
        self.ai_analysis_repo = ai_analysis_repo
        self.brain_snapshot_repo = brain_snapshot_repo
        self.incident_service = incident_service
        self.recommendation_service = recommendation_service
        self.report_audit_repo = report_audit_repo
        self.settings_getter = settings_getter or (lambda: None)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def build_context(self, demo_mode: bool) -> dict[str, object]:
        devices = self.device_repo.list_all(demo_mode=demo_mode)
        events = self.event_repo.list_recent(limit=200, demo_mode=demo_mode)
        alerts = self.alert_repo.list_all(demo_mode=demo_mode)
        policies = self.policy_service.list_entries()
        health = self.health_repo.list_all()
        analyses = self.ai_analysis_repo.list_recent(limit=5)
        brain_snapshot = self.brain_snapshot_repo.latest(demo_mode)
        brain_history = self.brain_snapshot_repo.list_recent(demo_mode, limit=5)
        incidents = self.incident_service.list_open(demo_mode) if self.incident_service is not None else []
        suggestions = (
            self.recommendation_service.list_pending(demo_mode, limit=12)
            if self.recommendation_service is not None
            else []
        )
        last_audit = self.report_audit_repo.latest(demo_mode) if self.report_audit_repo is not None else None
        risk_values = [device.risk_score for device in devices]
        settings = self.settings_getter()
        context = {
            "generated_at": utc_now(),
            "mode": "demo" if demo_mode else "real",
            "global_score": int(mean(risk_values)) if risk_values else 0,
            "settings": self._settings_summary(settings),
            "devices": [device.to_dict() for device in devices],
            "events": [event.to_dict() for event in events],
            "alerts": [alert.to_dict() for alert in alerts],
            "policies": [policy.to_dict() for policy in policies],
            "health": [status.to_dict() for status in health],
            "ai_analyses": [analysis.to_dict() for analysis in analyses],
            "incidents": [incident.to_dict() for incident in incidents],
            "suggestions": [entry.to_dict() for entry in suggestions],
            "brain_snapshot": brain_snapshot.to_dict() if brain_snapshot else None,
            "brain_history": [snapshot.to_dict() for snapshot in brain_history],
            "previous_audit": last_audit.to_dict() if last_audit else None,
            "event_chain_hash": self._event_chain_hash(events),
        }
        context["context_hash"] = self._hash_text(json.dumps(context, ensure_ascii=False, sort_keys=True))
        return context

    def build_ai_context(self, demo_mode: bool) -> dict[str, object]:
        context = self.build_context(demo_mode)
        devices = [USBDevice(**item) for item in context["devices"]]
        alerts = [Alert(**item) for item in context["alerts"]]
        events = [DeviceEvent(**item) for item in context["events"]]
        return {
            "generated_at": context["generated_at"],
            "mode": context["mode"],
            "global_score": context["global_score"],
            "context_hash": context["context_hash"],
            "summary": {
                "device_total": len(devices),
                "connected_total": len([device for device in devices if device.status == "connected"]),
                "new_device_total": len([device for device in devices if device.trust_state == "NEW"]),
                "deviation_total": len([device for device in devices if device.trust_state == "DEVIATION"]),
                "incident_total": len(context["incidents"]),
                "suggestion_total": len(context["suggestions"]),
                "alert_total": len(alerts),
            },
            "devices": [self._device_ai_view(device) for device in devices[:12]],
            "recent_events": [self._event_ai_view(event) for event in events[:20]],
            "alerts": [self._alert_ai_view(alert) for alert in alerts[:12]],
            "incidents": context["incidents"][:8],
            "suggestions": context["suggestions"][:8],
            "recent_ai_observations": [self._analysis_ai_view(item) for item in context["ai_analyses"][:3]],
            "brain_memory": self._brain_ai_view(context["brain_snapshot"]),
            "audit_integrity": {
                "event_chain_hash": context["event_chain_hash"],
                "previous_chain_hash": (context["previous_audit"] or {}).get("chain_hash"),
            },
        }

    def export_json(self, demo_mode: bool, filename: str | None = None) -> Path:
        target = self._resolve_target(filename, f"wirewall_audit_{utc_now().replace(':', '-')}.json")
        context = self.build_context(demo_mode)
        target.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")
        self._persist_export_audit(target, "json", context, demo_mode)
        return target

    def export_csv(self, demo_mode: bool, filename: str | None = None) -> Path:
        target = self._resolve_target(filename, f"wirewall_events_{utc_now().replace(':', '-')}.csv")
        events = self.event_repo.list_recent(limit=1000, demo_mode=demo_mode)
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["occurred_at", "event_type", "device_key", "summary", "severity", "score", "level", "source"],
            )
            writer.writeheader()
            for event in events:
                writer.writerow(
                    {
                        "occurred_at": event.occurred_at,
                        "event_type": event.event_type,
                        "device_key": event.device_key or "",
                        "summary": event.summary,
                        "severity": event.severity,
                        "score": event.score,
                        "level": event.level,
                        "source": event.source,
                    }
                )
        self._persist_export_audit(target, "csv", self.build_context(demo_mode), demo_mode)
        return target

    def export_html(self, demo_mode: bool, filename: str | None = None) -> Path:
        target = self._resolve_target(filename, f"wirewall_report_{utc_now().replace(':', '-')}.html")
        context = self.build_context(demo_mode)
        devices = [USBDevice(**item) for item in context["devices"]]
        events = [DeviceEvent(**item) for item in context["events"]]
        alerts = [Alert(**item) for item in context["alerts"]]
        policies = [PolicyEntry(**item) for item in context["policies"]]
        health = [HealthStatus(**item) for item in context["health"]]
        incidents = context["incidents"]
        suggestions = context["suggestions"]
        html_content = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Rapport WireWall</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background:#11161d; color:#eef3f8; margin:0; padding:32px; }}
    h1,h2 {{ margin:0 0 12px; }}
    .grid {{ display:grid; grid-template-columns: repeat(4, 1fr); gap:16px; margin:24px 0; }}
    .card {{ background:#19212b; padding:18px; border-radius:14px; border:1px solid #263241; }}
    table {{ width:100%; border-collapse: collapse; margin-top:12px; }}
    th, td {{ padding:10px; border-bottom:1px solid #263241; text-align:left; font-size:14px; }}
    th {{ color:#93a0b0; }}
    .section {{ margin-top:28px; }}
    .pill {{ display:inline-block; padding:4px 10px; border-radius:999px; background:#263241; }}
    code {{ color:#82d5ff; }}
  </style>
</head>
<body>
  <h1>WireWall - Rapport d'audit</h1>
  <p>Genere le {html_escape(context["generated_at"])} | Mode {html_escape(str(context["mode"]).upper())} | Score global {html_escape(str(context["global_score"]))}</p>
  <div class="grid">
    <div class="card"><h2>{len(devices)}</h2><div>Peripheriques</div></div>
    <div class="card"><h2>{len(events)}</h2><div>Evenements</div></div>
    <div class="card"><h2>{len(alerts)}</h2><div>Alertes</div></div>
    <div class="card"><h2>{len(incidents)}</h2><div>Incidents</div></div>
  </div>
  <div class="section">
    <h2>Integrite et audit</h2>
    <table>
      <tr><th>Hash contexte</th><td><code>{html_escape(context["context_hash"])}</code></td></tr>
      <tr><th>Chaînage evenements</th><td><code>{html_escape(context["event_chain_hash"])}</code></td></tr>
      <tr><th>Dernier audit</th><td><code>{html_escape((context["previous_audit"] or {}).get("chain_hash", "Aucun audit precedent"))}</code></td></tr>
      <tr><th>Profil actif</th><td>{html_escape(context["settings"]["security_profile"])}</td></tr>
      <tr><th>Modele IA</th><td>{html_escape(context["settings"]["ollama_model"])}</td></tr>
      <tr><th>Operateur</th><td>{html_escape(context["settings"]["author_name"] or "Non renseigne")}</td></tr>
    </table>
  </div>
  <div class="section">
    <h2>Alertes principales</h2>
    <table>
      <tr><th>Date</th><th>Gravite</th><th>Titre</th><th>Message</th></tr>
      {''.join(f"<tr><td>{html_escape(alert.created_at)}</td><td><span class='pill'>{html_escape(alert.severity)}</span></td><td>{html_escape(alert.title)}</td><td>{html_escape(alert.message)}</td></tr>" for alert in alerts[:20])}
    </table>
  </div>
  <div class="section">
    <h2>Peripheriques observes</h2>
    <table>
      <tr><th>VID:PID</th><th>Nom</th><th>Categorie</th><th>Confiance</th><th>Score</th><th>Etat</th></tr>
      {''.join(f"<tr><td>{html_escape(device.vid_pid)}</td><td>{html_escape(device.display_name)}</td><td>{html_escape(device.category)}</td><td>{html_escape(device.trust_state)}</td><td>{device.risk_score}</td><td>{html_escape(device.status)}</td></tr>" for device in devices[:50])}
    </table>
  </div>
  <div class="section">
    <h2>Incidents et decisions</h2>
    <table>
      <tr><th>Date</th><th>Device</th><th>Statut</th><th>Decision</th><th>Commentaire</th></tr>
      {''.join(f"<tr><td>{html_escape(item['created_at'])}</td><td>{html_escape(item.get('device_key') or '-')}</td><td>{html_escape(item.get('status') or '-')}</td><td>{html_escape(item.get('decision') or '-')}</td><td>{html_escape(item.get('comment') or '-')}</td></tr>" for item in incidents[:20])}
    </table>
  </div>
  <div class="section">
    <h2>Suggestions supervisees</h2>
    <table>
      <tr><th>Priorite</th><th>Titre</th><th>Action</th><th>Detail</th></tr>
      {''.join(f"<tr><td>{html_escape(item['priority'])}</td><td>{html_escape(item['title'])}</td><td>{html_escape(item['proposed_action'])}</td><td>{html_escape(item['details'])}</td></tr>" for item in suggestions[:20])}
    </table>
  </div>
  <div class="section">
    <h2>Synthese du moteur d'analyse continu</h2>
    <table>
      <tr><th>Niveau</th><th>Progression</th><th>Incidents</th><th>Resume</th></tr>
      <tr>
        <td>{html_escape(context["brain_snapshot"]["global_level"] if context["brain_snapshot"] else "N/A")}</td>
        <td>{html_escape(context["brain_snapshot"]["progress_status"] if context["brain_snapshot"] else "N/A")}</td>
        <td>{html_escape(context["brain_snapshot"]["incident_count"] if context["brain_snapshot"] else 0)}</td>
        <td>{html_escape(context["brain_snapshot"]["summary"] if context["brain_snapshot"] else "Aucune synthese disponible.")}</td>
      </tr>
    </table>
  </div>
  <div class="section">
    <h2>Sante de la plateforme</h2>
    <table>
      <tr><th>Composant</th><th>Etat</th><th>Detail</th></tr>
      {''.join(f"<tr><td>{html_escape(status.component)}</td><td>{html_escape(status.status)}</td><td>{html_escape(status.details)}</td></tr>" for status in health)}
    </table>
  </div>
</body>
</html>"""
        target.write_text(html_content, encoding="utf-8")
        self._persist_export_audit(target, "html", context, demo_mode)
        return target

    def _persist_export_audit(self, target: Path, export_format: str, context: dict[str, object], demo_mode: bool) -> None:
        file_sha = self._hash_file(target)
        if self.report_audit_repo is None:
            return
        previous = self.report_audit_repo.latest(demo_mode)
        chain_source = f"{previous.chain_hash if previous else 'GENESIS'}|{file_sha}|{context['context_hash']}|{export_format}"
        chain_hash = self._hash_text(chain_source)
        self._write_sidecar_hash(target, file_sha)
        audit = ReportAudit(
            created_at=utc_now(),
            export_format=export_format,
            file_path=str(target),
            file_sha256=file_sha,
            chain_hash=chain_hash,
            config_summary=context["settings"],
            demo_mode=demo_mode,
        )
        self.report_audit_repo.add(audit)

    def _write_sidecar_hash(self, target: Path, file_sha: str) -> None:
        sidecar = target.with_suffix(target.suffix + ".sha256.txt")
        sidecar.write_text(f"{file_sha}  {target.name}\n", encoding="utf-8")

    def _resolve_target(self, filename: str | None, fallback_name: str) -> Path:
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        if filename:
            target = Path(filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            return target
        return self.exports_dir / fallback_name

    def _settings_summary(self, settings) -> dict[str, object]:
        if settings is None:
            return {
                "security_profile": "Normal",
                "scan_interval_seconds": 0,
                "alert_threshold": 0,
                "ollama_model": "",
                "ollama_timeout_seconds": 0,
                "autostart_enabled": False,
                "desktop_notifications_enabled": True,
                "recommendation_mode": "balanced",
                "author_name": "",
                "organization_name": "",
            }
        return {
            "security_profile": settings.security_profile,
            "scan_interval_seconds": settings.scan_interval_seconds,
            "alert_threshold": settings.alert_threshold,
            "ollama_model": settings.ollama_model,
            "ollama_timeout_seconds": settings.ollama_timeout_seconds,
            "autostart_enabled": settings.autostart_enabled,
            "desktop_notifications_enabled": settings.desktop_notifications_enabled,
            "recommendation_mode": settings.recommendation_mode,
            "author_name": settings.author_name,
            "organization_name": settings.organization_name,
        }

    def _device_ai_view(self, device: USBDevice) -> dict[str, object]:
        return {
            "device_key": device.device_key,
            "vid_pid": device.vid_pid,
            "name": device.display_name,
            "category": device.category,
            "status": device.status,
            "risk_score": device.risk_score,
            "risk_level": device.risk_level,
            "confidence": round(device.confidence, 2),
            "source": device.identification_source,
            "serial_present": bool(device.serial_number),
            "trust_state": device.trust_state,
            "seen_count": device.seen_count,
            "last_decision": device.last_decision,
        }

    def _event_ai_view(self, event: DeviceEvent) -> dict[str, object]:
        return {
            "occurred_at": event.occurred_at,
            "event_type": event.event_type,
            "device_key": event.device_key,
            "summary": self._truncate(event.summary, 160),
            "severity": event.severity,
            "score": event.score,
            "level": event.level,
        }

    def _alert_ai_view(self, alert: Alert) -> dict[str, object]:
        return {
            "created_at": alert.created_at,
            "severity": alert.severity,
            "title": self._truncate(alert.title, 120),
            "message": self._truncate(alert.message, 180),
            "device_key": alert.device_key,
            "acknowledged": alert.acknowledged,
            "score": alert.score,
            "recommendations": alert.recommendations[:3],
            "case_id": alert.case_id,
        }

    def _brain_ai_view(self, snapshot: dict[str, object] | None) -> dict[str, object] | None:
        if snapshot is None:
            return None
        return {
            "created_at": snapshot["created_at"],
            "global_level": snapshot["global_level"],
            "progress_status": snapshot["progress_status"],
            "global_score": snapshot["global_score"],
            "incident_count": snapshot["incident_count"],
            "open_alert_count": snapshot["open_alert_count"],
            "summary": self._truncate(str(snapshot["summary"]), 260),
            "recommendations": snapshot["recommendations"][:4],
            "focus_areas": snapshot["focus_areas"][:5],
            "hot_devices": snapshot["metadata"].get("hot_devices", [])[:3],
        }

    def _analysis_ai_view(self, analysis: dict[str, object]) -> dict[str, object]:
        return {
            "created_at": analysis["created_at"],
            "model": analysis["model"],
            "global_level": analysis["global_level"],
            "summary": self._truncate(str(analysis["summary"]), 180),
            "success": analysis["success"],
        }

    def _event_chain_hash(self, events: list[DeviceEvent]) -> str:
        chain = "GENESIS"
        for event in sorted(events, key=lambda item: item.occurred_at):
            event_payload = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
            chain = self._hash_text(f"{chain}|{event_payload}")
        return chain

    def _hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _hash_text(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return value[: max_length - 3] + "..."


def html_escape(value: object) -> str:
    return html.escape(str(value), quote=True)
