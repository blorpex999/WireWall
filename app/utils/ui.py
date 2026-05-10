from __future__ import annotations

SEVERITY_COLORS = {
    "LOW": "#6BC46D",
    "MEDIUM": "#F6C344",
    "HIGH": "#FF944D",
    "CRITICAL": "#FF5D73",
    "CONNECTED": "#6BC46D",
    "DISCONNECTED": "#F6C344",
    "ENABLED": "#6BC46D",
    "BLOCKED": "#FF5D73",
    "PERMISSION_DENIED": "#F6C344",
    "INFO": "#4AB0FF",
    "OK": "#6BC46D",
    "WARNING": "#F6C344",
    "ERROR": "#FF5D73",
    "UNKNOWN": "#93A0B0",
    "NEW": "#4AB0FF",
    "RARE": "#F6C344",
    "KNOWN": "#6BC46D",
    "DEVIATION": "#FF944D",
}

CATEGORY_LABELS = {
    "storage": "Stockage",
    "hid": "HID",
    "hub": "Hub",
    "imaging": "Imagerie",
    "communication": "Communication",
    "vendor_specific": "Specifique",
    "unknown": "Inconnu",
}

DEVICE_STATUS_LABELS = {
    "connected": "Connecte",
    "disconnected": "Deconnecte",
    "enabled": "Autorise",
    "blocked": "Bloque",
    "permission_denied": "Droits insuffisants",
    "unknown": "Inconnu",
    "error": "Erreur",
}

HEALTH_STATUS_LABELS = {
    "ok": "OK",
    "warning": "A surveiller",
    "error": "Erreur",
    "unknown": "Inconnu",
}

POLICY_TYPE_LABELS = {
    "whitelist": "Liste blanche",
    "blacklist": "Liste noire",
}

MATCH_TYPE_LABELS = {
    "vid_pid": "VID:PID",
    "serial": "Numero de serie",
}

STATUS_TONES = {
    "connected": "OK",
    "disconnected": "WARNING",
    "enabled": "OK",
    "blocked": "CRITICAL",
    "permission_denied": "WARNING",
    "warning": "WARNING",
    "error": "ERROR",
    "ok": "OK",
    "unknown": "UNKNOWN",
}

TRUST_STATE_LABELS = {
    "NEW": "Nouveau",
    "RARE": "Rare",
    "KNOWN": "Connu",
    "DEVIATION": "Deviation",
}

TRUST_STATE_TONES = {
    "NEW": "INFO",
    "RARE": "WARNING",
    "KNOWN": "OK",
    "DEVIATION": "HIGH",
}

DECISION_LABELS = {
    "none": "Aucune",
    "whitelist": "Whitelist",
    "blacklist": "Blacklist",
    "watch": "Surveiller",
    "trust": "Connu fiable",
    "trusted": "Connu fiable",
    "ignore_temporary": "Ignorer temporairement",
}

INCIDENT_STATUS_LABELS = {
    "new": "Nouvelle",
    "investigating": "En cours",
    "false_positive": "Fausse alerte",
    "resolved": "Resolue",
}

INCIDENT_STATUS_TONES = {
    "new": "WARNING",
    "investigating": "HIGH",
    "false_positive": "INFO",
    "resolved": "OK",
}

RECOMMENDATION_PRIORITY_LABELS = {
    "LOW": "Basse",
    "MEDIUM": "Moyenne",
    "HIGH": "Haute",
    "CRITICAL": "Critique",
}


def severity_color(level: str) -> str:
    return SEVERITY_COLORS.get(level.upper(), SEVERITY_COLORS["UNKNOWN"])


def bool_text(value: bool) -> str:
    return "Oui" if value else "Non"


def category_text(value: str) -> str:
    return CATEGORY_LABELS.get(value, value or "Inconnu")


def device_status_text(value: str) -> str:
    return DEVICE_STATUS_LABELS.get(value, value or "Inconnu")


def health_status_text(value: str) -> str:
    return HEALTH_STATUS_LABELS.get(value, value or "Inconnu")


def policy_type_text(value: str) -> str:
    return POLICY_TYPE_LABELS.get(value, value or "Inconnu")


def match_type_text(value: str) -> str:
    return MATCH_TYPE_LABELS.get(value, value or value)


def tone_for_status(status: str) -> str:
    return STATUS_TONES.get(status.lower(), "INFO")


def trust_state_text(value: str) -> str:
    return TRUST_STATE_LABELS.get((value or "").upper(), value or "Inconnu")


def trust_state_tone(value: str) -> str:
    return TRUST_STATE_TONES.get((value or "").upper(), "INFO")


def decision_text(value: str) -> str:
    return DECISION_LABELS.get((value or "").lower(), value or "Aucune")


def incident_status_text(value: str) -> str:
    return INCIDENT_STATUS_LABELS.get((value or "").lower(), value or "Inconnu")


def incident_status_tone(value: str) -> str:
    return INCIDENT_STATUS_TONES.get((value or "").lower(), "INFO")


def recommendation_priority_text(value: str) -> str:
    return RECOMMENDATION_PRIORITY_LABELS.get((value or "").upper(), value or "Inconnue")


def risk_level_from_score(score: int) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def shorten_text(value: str, limit: int = 88) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."
