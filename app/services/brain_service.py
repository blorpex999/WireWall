from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from app.models.entities import BrainSnapshot
from app.utils.datetime import hours_ago, parse_timestamp, utc_now


class BrainService:
    def __init__(
        self,
        device_repo,
        event_repo,
        alert_repo,
        health_repo,
        ai_analysis_repo,
        brain_snapshot_repo,
    ) -> None:
        self.device_repo = device_repo
        self.event_repo = event_repo
        self.alert_repo = alert_repo
        self.health_repo = health_repo
        self.ai_analysis_repo = ai_analysis_repo
        self.brain_snapshot_repo = brain_snapshot_repo

    def refresh(self, demo_mode: bool) -> BrainSnapshot:
        devices = self.device_repo.list_all(demo_mode=demo_mode)
        events = self.event_repo.list_recent(limit=500, demo_mode=demo_mode)
        alerts = self.alert_repo.list_all(demo_mode=demo_mode)
        health = self.health_repo.list_all()
        analyses = self.ai_analysis_repo.list_recent(limit=5)
        previous = self.brain_snapshot_repo.latest(demo_mode)

        recent_events = self._filter_since(events, hours_ago(24))
        event_counts = Counter(event.device_key for event in recent_events if event.device_key)
        reconnect_counts = Counter(
            event.device_key
            for event in recent_events
            if event.device_key and event.event_type in {"connected", "disconnected"}
        )
        open_alerts = [alert for alert in alerts if not alert.acknowledged]
        critical_alerts = [alert for alert in open_alerts if alert.severity == "CRITICAL"]
        high_alerts = [alert for alert in open_alerts if alert.severity in {"HIGH", "CRITICAL"}]
        high_risk_devices = [device for device in devices if device.risk_level in {"HIGH", "CRITICAL"}]
        unstable_device_keys = {key for key, count in reconnect_counts.items() if count >= 4}
        degraded_components = [status.component for status in health if status.status not in {"ok", "unknown"}]

        device_index = {device.device_key: device for device in devices}
        hot_devices = self._build_hot_devices(device_index, event_counts, open_alerts)
        global_score = int(mean([device.risk_score for device in devices])) if devices else 0
        global_level = self._compute_level(global_score, critical_alerts, high_alerts, high_risk_devices)
        incident_count = len(
            {
                *[device.device_key for device in high_risk_devices],
                *unstable_device_keys,
                *[alert.device_key for alert in open_alerts if alert.device_key],
            }
        )
        progress_status = self._compute_progress(previous, global_score, incident_count, len(open_alerts))
        summary = self._build_summary(
            global_level=global_level,
            progress_status=progress_status,
            device_total=len(devices),
            connected_total=len([device for device in devices if device.status == "connected"]),
            incident_count=incident_count,
            open_alert_count=len(open_alerts),
            hot_devices=hot_devices,
            degraded_components=degraded_components,
        )
        recommendations = self._build_recommendations(
            critical_alerts=critical_alerts,
            unstable_device_keys=unstable_device_keys,
            high_risk_devices=high_risk_devices,
            degraded_components=degraded_components,
            analyses=analyses,
        )
        focus_areas = self._build_focus_areas(hot_devices, degraded_components, open_alerts)
        snapshot = BrainSnapshot(
            created_at=utc_now(),
            global_score=global_score,
            global_level=global_level,
            progress_status=progress_status,
            summary=summary,
            incident_count=incident_count,
            open_alert_count=len(open_alerts),
            monitored_device_count=len(devices),
            recommendations=recommendations,
            focus_areas=focus_areas,
            metadata={
                "hot_devices": hot_devices[:5],
                "unstable_device_keys": sorted(unstable_device_keys),
                "degraded_components": degraded_components,
                "high_alert_total": len(high_alerts),
                "analysis_success_rate": self._analysis_success_rate(analyses),
            },
            demo_mode=demo_mode,
        )

        if self._should_store(previous, snapshot):
            snapshot.id = self.brain_snapshot_repo.add(snapshot)
            return snapshot
        return previous or snapshot

    def latest(self, demo_mode: bool) -> BrainSnapshot | None:
        return self.brain_snapshot_repo.latest(demo_mode)

    def recent(self, demo_mode: bool, limit: int = 5) -> list[BrainSnapshot]:
        return self.brain_snapshot_repo.list_recent(demo_mode, limit=limit)

    def _filter_since(self, events, since: str):
        cutoff = parse_timestamp(since)
        if cutoff is None:
            return list(events)
        filtered = []
        for event in events:
            occurred_at = parse_timestamp(event.occurred_at)
            if occurred_at is not None and occurred_at >= cutoff:
                filtered.append(event)
        return filtered

    def _build_hot_devices(self, device_index, event_counts, open_alerts) -> list[dict[str, object]]:
        alert_counts: dict[str, int] = defaultdict(int)
        for alert in open_alerts:
            if alert.device_key:
                alert_counts[alert.device_key] += 1

        rows: list[dict[str, object]] = []
        for device_key, device in device_index.items():
            event_count = event_counts.get(device_key, 0)
            alert_count = alert_counts.get(device_key, 0)
            heat = int(device.risk_score + (event_count * 8) + (alert_count * 18))
            if heat <= 0 and device.status != "connected":
                continue
            rows.append(
                {
                    "device_key": device_key,
                    "name": device.display_name,
                    "risk_level": device.risk_level,
                    "risk_score": device.risk_score,
                    "event_count_24h": event_count,
                    "open_alerts": alert_count,
                    "heat": heat,
                }
            )
        rows.sort(key=lambda row: (row["heat"], row["open_alerts"], row["risk_score"]), reverse=True)
        return rows

    def _compute_level(self, global_score: int, critical_alerts, high_alerts, high_risk_devices) -> str:
        if critical_alerts:
            return "CRITICAL"
        if high_alerts or high_risk_devices or global_score >= 50:
            return "HIGH"
        if global_score >= 25:
            return "MEDIUM"
        return "LOW"

    def _compute_progress(
        self,
        previous: BrainSnapshot | None,
        global_score: int,
        incident_count: int,
        open_alert_count: int,
    ) -> str:
        if previous is None:
            return "LEARNING"
        if incident_count > previous.incident_count or open_alert_count > previous.open_alert_count or global_score > previous.global_score + 5:
            return "DETERIORATING"
        if incident_count < previous.incident_count or open_alert_count < previous.open_alert_count or global_score + 5 < previous.global_score:
            return "IMPROVING"
        return "STABLE"

    def _build_summary(
        self,
        *,
        global_level: str,
        progress_status: str,
        device_total: int,
        connected_total: int,
        incident_count: int,
        open_alert_count: int,
        hot_devices: list[dict[str, object]],
        degraded_components: list[str],
    ) -> str:
        hot_names = ", ".join(item["name"] for item in hot_devices[:3]) if hot_devices else "aucun point chaud majeur"
        degraded = ", ".join(degraded_components[:3]) if degraded_components else "aucun composant degrade"
        return (
            f"Niveau {global_level}. Le moteur suit {incident_count} incident(s) actif(s) "
            f"sur {connected_total}/{device_total} peripherique(s) connecte(s), avec {open_alert_count} alerte(s) ouverte(s). "
            f"Progression {progress_status.lower()}. Points chauds: {hot_names}. Sante plateforme: {degraded}."
        )

    def _build_recommendations(
        self,
        *,
        critical_alerts,
        unstable_device_keys: set[str],
        high_risk_devices,
        degraded_components: list[str],
        analyses,
    ) -> list[str]:
        recommendations: list[str] = []
        if critical_alerts:
            recommendations.append("Traiter immediatement les alertes CRITICAL avant tout branchement supplementaire.")
        if unstable_device_keys:
            recommendations.append("Verifier les reconnexions repetitives et confirmer la legitimite des peripheriques instables.")
        if high_risk_devices:
            recommendations.append("Identifier ou isoler les peripheriques a risque HIGH/CRITICAL avant validation utilisateur.")
        if degraded_components:
            recommendations.append(f"Corriger les composants degrades: {', '.join(degraded_components[:3])}.")
        if analyses and not analyses[0].success:
            recommendations.append("Relancer une analyse IA locale pour enrichir le diagnostic courant.")
        if not recommendations:
            recommendations.append("Maintenir la surveillance continue et conserver la base de reference actuelle.")
        return recommendations[:5]

    def _build_focus_areas(self, hot_devices: list[dict[str, object]], degraded_components: list[str], open_alerts) -> list[str]:
        focus = [item["name"] for item in hot_devices[:3]]
        focus.extend(f"Composant {component}" for component in degraded_components[:2])
        if open_alerts and len(focus) < 5:
            focus.append(f"{len(open_alerts)} alerte(s) ouverte(s)")
        return focus[:5] or ["Surveillance USB courante"]

    def _analysis_success_rate(self, analyses) -> float:
        if not analyses:
            return 0.0
        success_count = len([analysis for analysis in analyses if analysis.success])
        return round(success_count / len(analyses), 2)

    def _should_store(self, previous: BrainSnapshot | None, current: BrainSnapshot) -> bool:
        if previous is None:
            return True
        return any(
            [
                previous.global_score != current.global_score,
                previous.global_level != current.global_level,
                previous.progress_status != current.progress_status,
                previous.incident_count != current.incident_count,
                previous.open_alert_count != current.open_alert_count,
                previous.summary != current.summary,
                previous.focus_areas != current.focus_areas,
                previous.recommendations != current.recommendations,
            ]
        )
