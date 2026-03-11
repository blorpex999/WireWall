from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from statistics import mean

from app.models.entities import Alert, DeviceEvent, HealthStatus, PolicyEntry, USBDevice
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
    ) -> None:
        self.exports_dir = exports_dir
        self.device_repo = device_repo
        self.event_repo = event_repo
        self.policy_service = policy_service
        self.alert_repo = alert_repo
        self.health_repo = health_repo
        self.ai_analysis_repo = ai_analysis_repo
        self.brain_snapshot_repo = brain_snapshot_repo
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
        risk_values = [device.risk_score for device in devices]
        return {
            "generated_at": utc_now(),
            "mode": "demo" if demo_mode else "real",
            "global_score": int(mean(risk_values)) if risk_values else 0,
            "devices": [device.to_dict() for device in devices],
            "events": [event.to_dict() for event in events],
            "alerts": [alert.to_dict() for alert in alerts],
            "policies": [policy.to_dict() for policy in policies],
            "health": [status.to_dict() for status in health],
            "ai_analyses": [analysis.to_dict() for analysis in analyses],
            "brain_snapshot": brain_snapshot.to_dict() if brain_snapshot else None,
            "brain_history": [snapshot.to_dict() for snapshot in brain_history],
        }

    def build_ai_context(self, demo_mode: bool) -> dict[str, object]:
        devices = self.device_repo.list_all(demo_mode=demo_mode)
        events = self.event_repo.list_recent(limit=25, demo_mode=demo_mode)
        alerts = self.alert_repo.list_all(demo_mode=demo_mode)[:12]
        policies = self.policy_service.list_entries()
        health = self.health_repo.list_all()
        analyses = self.ai_analysis_repo.list_recent(limit=3)
        brain_snapshot = self.brain_snapshot_repo.latest(demo_mode)

        risk_values = [device.risk_score for device in devices]
        connected_devices = [device for device in devices if device.status == "connected"]
        critical_devices = [device for device in devices if device.risk_level in {"HIGH", "CRITICAL"}]
        high_alerts = [alert for alert in alerts if alert.severity in {"HIGH", "CRITICAL"}]

        return {
            "generated_at": utc_now(),
            "mode": "demo" if demo_mode else "real",
            "global_score": int(mean(risk_values)) if risk_values else 0,
            "summary": {
                "device_total": len(devices),
                "connected_total": len(connected_devices),
                "high_risk_devices": len(critical_devices),
                "alert_total": len(alerts),
                "high_alert_total": len(high_alerts),
                "policy_total": len(policies),
                "whitelist_total": len([policy for policy in policies if policy.policy_type == "whitelist"]),
                "blacklist_total": len([policy for policy in policies if policy.policy_type == "blacklist"]),
            },
            "devices": [self._device_ai_view(device) for device in devices[:12]],
            "recent_events": [self._event_ai_view(event) for event in events[:20]],
            "alerts": [self._alert_ai_view(alert) for alert in alerts],
            "health": [self._health_ai_view(status) for status in health],
            "policies": [self._policy_ai_view(policy) for policy in policies[:20]],
            "recent_ai_observations": [self._analysis_ai_view(analysis) for analysis in analyses],
            "brain_memory": self._brain_ai_view(brain_snapshot),
        }

    def export_json(self, demo_mode: bool, filename: str | None = None) -> Path:
        target = self._resolve_target(filename, f"wirewall_audit_{utc_now().replace(':', '-')}.json")
        target.write_text(
            json.dumps(self.build_context(demo_mode), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
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
        return target

    def export_html(self, demo_mode: bool, filename: str | None = None) -> Path:
        target = self._resolve_target(filename, f"wirewall_report_{utc_now().replace(':', '-')}.html")
        context = self.build_context(demo_mode)
        devices = [USBDevice(**item) for item in context["devices"]]
        events = [DeviceEvent(**item) for item in context["events"]]
        alerts = [Alert(**item) for item in context["alerts"]]
        policies = [PolicyEntry(**item) for item in context["policies"]]
        health = [HealthStatus(**item) for item in context["health"]]
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
  </style>
</head>
<body>
  <h1>WireWall - Rapport d'audit</h1>
  <p>Genere le {html_escape(context["generated_at"])} | Mode {html_escape(str(context["mode"]).upper())} | Score global {html_escape(str(context["global_score"]))}</p>
  <div class="grid">
    <div class="card"><h2>{len(devices)}</h2><div>Peripheriques</div></div>
    <div class="card"><h2>{len(events)}</h2><div>Evenements</div></div>
    <div class="card"><h2>{len(alerts)}</h2><div>Alertes</div></div>
    <div class="card"><h2>{len(policies)}</h2><div>Policies</div></div>
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
      <tr><th>VID:PID</th><th>Nom</th><th>Categorie</th><th>Score</th><th>Etat</th></tr>
      {''.join(f"<tr><td>{html_escape(device.vid_pid)}</td><td>{html_escape(device.display_name)}</td><td>{html_escape(device.category)}</td><td>{device.risk_score}</td><td>{html_escape(device.status)}</td></tr>" for device in devices[:50])}
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
        return target

    def _resolve_target(self, filename: str | None, fallback_name: str) -> Path:
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        if filename:
            target = Path(filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            return target
        return self.exports_dir / fallback_name

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
        }

    def _policy_ai_view(self, policy: PolicyEntry) -> dict[str, object]:
        return {
            "policy_type": policy.policy_type,
            "match_type": policy.match_type,
            "value": policy.value,
            "label": policy.label,
            "enabled": policy.enabled,
        }

    def _health_ai_view(self, status: HealthStatus) -> dict[str, object]:
        return {
            "component": status.component,
            "status": status.status,
            "details": self._truncate(status.details, 160),
        }

    def _analysis_ai_view(self, analysis) -> dict[str, object]:
        return {
            "created_at": analysis.created_at,
            "model": analysis.model,
            "global_level": analysis.global_level,
            "summary": self._truncate(analysis.summary, 220),
            "success": analysis.success,
        }

    def _brain_ai_view(self, snapshot) -> dict[str, object] | None:
        if snapshot is None:
            return None
        return {
            "created_at": snapshot.created_at,
            "global_level": snapshot.global_level,
            "progress_status": snapshot.progress_status,
            "global_score": snapshot.global_score,
            "incident_count": snapshot.incident_count,
            "open_alert_count": snapshot.open_alert_count,
            "summary": self._truncate(snapshot.summary, 260),
            "recommendations": snapshot.recommendations[:4],
            "focus_areas": snapshot.focus_areas[:5],
            "hot_devices": snapshot.metadata.get("hot_devices", [])[:3],
        }

    def _truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return value[: max_length - 3] + "..."


def html_escape(value: object) -> str:
    return html.escape(str(value), quote=True)
