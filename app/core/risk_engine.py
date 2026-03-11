from __future__ import annotations

from collections import Counter
from typing import Any

from app.config.defaults import PROFILE_PRESETS
from app.core.constants import HIGH_MAX, LOW_MAX, MEDIUM_MAX
from app.models.entities import RiskAssessment, USBDevice
from app.utils.datetime import parse_timestamp


class RiskEngine:
    def assess(
        self,
        device: USBDevice,
        recent_events: list[dict[str, Any]],
        policies: dict[str, Any],
        profile: str,
        now: str,
    ) -> RiskAssessment:
        preset = PROFILE_PRESETS.get(profile, PROFILE_PRESETS["Normal"])
        reasons: list[str] = []
        recommendations: list[str] = []
        score = 0

        if policies.get("is_blacklisted"):
            score += 90
            reasons.append("Le périphérique correspond à une entrée blacklist.")
            recommendations.append("Retirer immédiatement le périphérique et conserver la preuve.")

        if device.category == "storage" and not policies.get("is_whitelisted"):
            score += 45
            reasons.append("Stockage USB non autorisé détecté.")
            recommendations.append("Vérifier la légitimité du support avant accès au poste.")

        if device.category == "hid" and not policies.get("is_whitelisted"):
            score += 35
            reasons.append("Périphérique HID inconnu ou non approuvé.")
            recommendations.append("Valider l'utilisateur et le périphérique avant usage.")

        reconnect_count = self._count_recent_connects(recent_events)
        reconnect_penalty = int(preset["reconnect_penalty"])
        if reconnect_count >= 3:
            score += reconnect_penalty
            reasons.append(f"Reconnexions fréquentes observées ({reconnect_count} sur la fenêtre récente).")
            recommendations.append("Surveiller une éventuelle tentative d'évasion ou de test d'accès.")

        if self._is_atypical_hour(now):
            score += 10
            reasons.append("Connexion sur un horaire atypique.")
            recommendations.append("Confirmer que l'activité est attendue pour ce créneau.")

        missing_chunks = 0
        if not device.vendor_name or device.vendor_name == "Inconnu":
            missing_chunks += 1
        if not device.product_name or device.product_name == "Périphérique USB":
            missing_chunks += 1
        if not device.serial_number:
            missing_chunks += 1
        if missing_chunks:
            metadata_penalty = int(preset["metadata_penalty"])
            applied = min(missing_chunks * metadata_penalty, 15)
            score += applied
            reasons.append("Métadonnées incomplètes ou non accessibles.")
            recommendations.append("Compléter l'identification avant autorisation définitive.")

        if policies.get("is_whitelisted"):
            score -= 35
            reasons.append("Le périphérique est présent en whitelist.")

        if policies.get("is_known_device"):
            score -= 10
            reasons.append("Le périphérique est connu et déjà observé.")

        score = max(0, min(100, score))
        level = self._score_to_level(score)

        if not recommendations:
            recommendations.append("Aucune action immédiate requise. Continuer la surveillance.")

        return RiskAssessment(
            assessed_at=now,
            device_key=device.device_key,
            score=score,
            level=level,
            reasons=reasons or ["Aucun indicateur de risque majeur détecté."],
            recommendations=recommendations,
            profile_name=profile,
            metadata={"recent_connects": reconnect_count, "policy_summary": policies},
        )

    def _count_recent_connects(self, recent_events: list[dict[str, Any]]) -> int:
        counter = Counter(event.get("event_type") for event in recent_events)
        return counter.get("connected", 0)

    def _is_atypical_hour(self, now: str) -> bool:
        parsed = parse_timestamp(now)
        if parsed is None:
            return False
        hour = parsed.astimezone().hour
        return hour < 6 or hour >= 21

    def _score_to_level(self, score: int) -> str:
        if score <= LOW_MAX:
            return "LOW"
        if score <= MEDIUM_MAX:
            return "MEDIUM"
        if score <= HIGH_MAX:
            return "HIGH"
        return "CRITICAL"
