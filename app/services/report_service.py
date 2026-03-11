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
    ) -> None:
        self.exports_dir = exports_dir
        self.device_repo = device_repo
        self.event_repo = event_repo
        self.policy_service = policy_service
        self.alert_repo = alert_repo
        self.health_repo = health_repo
        self.ai_analysis_repo = ai_analysis_repo
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def build_context(self, demo_mode: bool) -> dict[str, object]:
        devices = self.device_repo.list_all(demo_mode=demo_mode)
        events = self.event_repo.list_recent(limit=200, demo_mode=demo_mode)
        alerts = self.alert_repo.list_all(demo_mode=demo_mode)
        policies = self.policy_service.list_entries()
        health = self.health_repo.list_all()
        analyses = self.ai_analysis_repo.list_recent(limit=5)
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
        html = f"""<!doctype html>
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
  <p>Généré le {html_escape(context["generated_at"])} | Mode {html_escape(str(context["mode"]).upper())} | Score global {html_escape(str(context["global_score"]))}</p>
  <div class="grid">
    <div class="card"><h2>{len(devices)}</h2><div>Périphériques</div></div>
    <div class="card"><h2>{len(events)}</h2><div>Evénements</div></div>
    <div class="card"><h2>{len(alerts)}</h2><div>Alertes</div></div>
    <div class="card"><h2>{len(policies)}</h2><div>Policies</div></div>
  </div>
  <div class="section">
    <h2>Alertes principales</h2>
    <table>
      <tr><th>Date</th><th>Gravité</th><th>Titre</th><th>Message</th></tr>
      {''.join(f"<tr><td>{html_escape(alert.created_at)}</td><td><span class='pill'>{html_escape(alert.severity)}</span></td><td>{html_escape(alert.title)}</td><td>{html_escape(alert.message)}</td></tr>" for alert in alerts[:20])}
    </table>
  </div>
  <div class="section">
    <h2>Périphériques observés</h2>
    <table>
      <tr><th>VID:PID</th><th>Nom</th><th>Catégorie</th><th>Score</th><th>Etat</th></tr>
      {''.join(f"<tr><td>{html_escape(device.vid_pid)}</td><td>{html_escape(device.display_name)}</td><td>{html_escape(device.category)}</td><td>{device.risk_score}</td><td>{html_escape(device.status)}</td></tr>" for device in devices[:50])}
    </table>
  </div>
  <div class="section">
    <h2>Santé de la plateforme</h2>
    <table>
      <tr><th>Composant</th><th>Etat</th><th>Détail</th></tr>
      {''.join(f"<tr><td>{html_escape(status.component)}</td><td>{html_escape(status.status)}</td><td>{html_escape(status.details)}</td></tr>" for status in health)}
    </table>
  </div>
</body>
</html>"""
        target.write_text(html, encoding="utf-8")
        return target

    def _resolve_target(self, filename: str | None, fallback_name: str) -> Path:
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        if filename:
            target = Path(filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            return target
        return self.exports_dir / fallback_name


def html_escape(value: object) -> str:
    return html.escape(str(value), quote=True)
