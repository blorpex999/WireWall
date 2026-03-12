from __future__ import annotations

from app.models.entities import RecommendationEntry
from app.utils.datetime import utc_now


MODE_THRESHOLDS = {
    "conservative": {"known_for_whitelist": 6, "trust_score_cap": 20},
    "balanced": {"known_for_whitelist": 4, "trust_score_cap": 25},
    "proactive": {"known_for_whitelist": 3, "trust_score_cap": 30},
}


class RecommendationService:
    def __init__(self, recommendation_repo, device_repo, alert_repo, policy_service, operator_name_getter) -> None:
        self.recommendation_repo = recommendation_repo
        self.device_repo = device_repo
        self.alert_repo = alert_repo
        self.policy_service = policy_service
        self.operator_name_getter = operator_name_getter

    def refresh(self, demo_mode: bool, mode: str = "balanced") -> list[RecommendationEntry]:
        thresholds = MODE_THRESHOLDS.get(mode, MODE_THRESHOLDS["balanced"])
        devices = self.device_repo.list_all(demo_mode=demo_mode)
        open_alerts = [alert for alert in self.alert_repo.list_all(demo_mode=demo_mode) if not alert.acknowledged]
        alert_device_keys = {alert.device_key for alert in open_alerts if alert.device_key}
        active_keys: set[str] = set()
        now = utc_now()

        for device in devices:
            policies = self.policy_service.evaluate_device(device)
            if self._should_whitelist(device, policies, alert_device_keys, thresholds):
                entry = RecommendationEntry(
                    stable_key=f"whitelist:{device.device_key}",
                    created_at=now,
                    updated_at=now,
                    recommendation_type="baseline_whitelist",
                    priority="MEDIUM",
                    title=f"Whitelister {device.display_name}",
                    details="Peripherique habituel, stable et sans incident ouvert. Une whitelist reduira le bruit operationnel.",
                    proposed_action="whitelist_device",
                    target_device_key=device.device_key,
                    context={
                        "seen_count": device.seen_count,
                        "trust_state": device.trust_state,
                        "risk_score": device.risk_score,
                    },
                    demo_mode=demo_mode,
                )
                entry.id = self.recommendation_repo.upsert(entry)
                active_keys.add(entry.stable_key)

            if self._should_blacklist(device, policies):
                entry = RecommendationEntry(
                    stable_key=f"blacklist:{device.device_key}",
                    created_at=now,
                    updated_at=now,
                    recommendation_type="suspicious_storage",
                    priority="HIGH",
                    title=f"Blacklister {device.display_name}",
                    details="Stockage non approuve avec niveau de risque eleve ou deviation recente. Une blacklist est recommandee apres validation analyste.",
                    proposed_action="blacklist_device",
                    target_device_key=device.device_key,
                    context={
                        "seen_count": device.seen_count,
                        "trust_state": device.trust_state,
                        "risk_level": device.risk_level,
                    },
                    demo_mode=demo_mode,
                )
                entry.id = self.recommendation_repo.upsert(entry)
                active_keys.add(entry.stable_key)

            if self._should_trust(device, policies, thresholds):
                entry = RecommendationEntry(
                    stable_key=f"trust:{device.device_key}",
                    created_at=now,
                    updated_at=now,
                    recommendation_type="lower_noise",
                    priority="LOW",
                    title=f"Marquer {device.display_name} comme habituel",
                    details="Le peripherique est observe frequemment, reste stable et peut etre traite comme connu pour reduire le bruit de surveillance.",
                    proposed_action="trust_device",
                    target_device_key=device.device_key,
                    context={
                        "seen_count": device.seen_count,
                        "trust_state": device.trust_state,
                        "risk_score": device.risk_score,
                    },
                    demo_mode=demo_mode,
                )
                entry.id = self.recommendation_repo.upsert(entry)
                active_keys.add(entry.stable_key)

        self.recommendation_repo.expire_missing(active_keys, demo_mode, updated_at=now)
        return self.recommendation_repo.list_all(status="pending", demo_mode=demo_mode, limit=12)

    def list_pending(self, demo_mode: bool, limit: int = 12) -> list[RecommendationEntry]:
        return self.recommendation_repo.list_all(status="pending", demo_mode=demo_mode, limit=limit)

    def count_pending(self, demo_mode: bool) -> int:
        return self.recommendation_repo.count_pending(demo_mode)

    def accept(self, recommendation_id: int) -> RecommendationEntry:
        recommendation = self.recommendation_repo.get(recommendation_id)
        if recommendation is None:
            raise ValueError("Suggestion introuvable.")
        self._apply_action(recommendation)
        self.recommendation_repo.update_status(recommendation_id, "accepted", self._operator_name(), updated_at=utc_now())
        return self.recommendation_repo.get(recommendation_id) or recommendation

    def reject(self, recommendation_id: int, comment: str = "") -> RecommendationEntry:
        recommendation = self.recommendation_repo.get(recommendation_id)
        if recommendation is None:
            raise ValueError("Suggestion introuvable.")
        self.recommendation_repo.update_status(recommendation_id, "rejected", comment or self._operator_name(), updated_at=utc_now())
        return self.recommendation_repo.get(recommendation_id) or recommendation

    def defer(self, recommendation_id: int, comment: str = "") -> RecommendationEntry:
        recommendation = self.recommendation_repo.get(recommendation_id)
        if recommendation is None:
            raise ValueError("Suggestion introuvable.")
        self.recommendation_repo.update_status(recommendation_id, "deferred", comment or self._operator_name(), updated_at=utc_now())
        return self.recommendation_repo.get(recommendation_id) or recommendation

    def _apply_action(self, recommendation: RecommendationEntry) -> None:
        device_key = recommendation.target_device_key
        if not device_key:
            return
        device = self.device_repo.get(device_key)
        if device is None:
            raise ValueError("Peripherique cible introuvable pour cette suggestion.")

        if recommendation.proposed_action == "whitelist_device":
            value = device.serial_number if device.serial_number else device.vid_pid
            match_type = "serial" if device.serial_number else "vid_pid"
            self.policy_service.add_entry(
                policy_type="whitelist",
                match_type=match_type,
                value=value,
                label=device.display_name,
                notes="Suggestion acceptee depuis WireWall",
            )
            self.device_repo.update_decision(device.device_key, "whitelist")
        elif recommendation.proposed_action == "blacklist_device":
            value = device.serial_number if device.serial_number else device.vid_pid
            match_type = "serial" if device.serial_number else "vid_pid"
            self.policy_service.add_entry(
                policy_type="blacklist",
                match_type=match_type,
                value=value,
                label=device.display_name,
                notes="Suggestion acceptee depuis WireWall",
            )
            self.device_repo.update_decision(device.device_key, "blacklist")
        elif recommendation.proposed_action == "trust_device":
            self.device_repo.update_decision(device.device_key, "trusted")

    def _should_whitelist(self, device, policies, alert_device_keys: set[str], thresholds: dict[str, int]) -> bool:
        return bool(
            device.status == "connected"
            and device.trust_state == "KNOWN"
            and device.seen_count >= thresholds["known_for_whitelist"]
            and device.device_key not in alert_device_keys
            and not policies.get("is_whitelisted")
            and device.category in {"hid", "communication", "hub"}
        )

    def _should_blacklist(self, device, policies) -> bool:
        return bool(
            device.category == "storage"
            and device.trust_state in {"NEW", "RARE", "DEVIATION"}
            and device.risk_level in {"HIGH", "CRITICAL"}
            and not policies.get("is_blacklisted")
        )

    def _should_trust(self, device, policies, thresholds: dict[str, int]) -> bool:
        return bool(
            device.trust_state == "KNOWN"
            and device.risk_score <= thresholds["trust_score_cap"]
            and device.last_decision not in {"trusted", "whitelist"}
            and not policies.get("is_whitelisted")
        )

    def _operator_name(self) -> str:
        value = self.operator_name_getter().strip()
        return value or "Operateur local"
