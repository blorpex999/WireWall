from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from app.infrastructure.database import DatabaseManager
from app.models.entities import (
    AIAnalysis,
    Alert,
    AppSettings,
    DeviceEvent,
    HealthStatus,
    PolicyEntry,
    RiskAssessment,
    USBDevice,
)


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().upper()


def _is_generic_vendor(value: str | None) -> bool:
    return _normalize_text(value) in {"", "INCONNU", "UNKNOWN"}


def _is_generic_product(value: str | None) -> bool:
    return _normalize_text(value) in {"", "PÉRIPHÉRIQUE USB", "PERIPHERIQUE USB", "USB DEVICE", "UNKNOWN"}


class DeviceRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def upsert(self, device: USBDevice) -> None:
        payload = asdict(device)
        payload["metadata_json"] = _dumps(payload.pop("metadata"))
        payload["demo_mode"] = int(payload["demo_mode"])
        columns = ", ".join(payload.keys())
        placeholders = ", ".join(f":{key}" for key in payload)
        updates = ", ".join(f"{key}=excluded.{key}" for key in payload if key != "device_key")
        with self.db.session() as connection:
            connection.execute(
                f"""
                INSERT INTO devices ({columns})
                VALUES ({placeholders})
                ON CONFLICT(device_key) DO UPDATE SET {updates}
                """,
                payload,
            )

    def list_all(
        self,
        *,
        search: str = "",
        category: str = "",
        status: str = "",
        demo_mode: bool | None = None,
    ) -> list[USBDevice]:
        conditions = []
        params: dict[str, Any] = {}
        if search:
            conditions.append(
                "(device_key LIKE :search OR vendor_name LIKE :search OR product_name LIKE :search OR serial_number LIKE :search)"
            )
            params["search"] = f"%{search}%"
        if category:
            conditions.append("category = :category")
            params["category"] = category
        if status:
            conditions.append("status = :status")
            params["status"] = status
        if demo_mode is not None:
            conditions.append("demo_mode = :demo_mode")
            params["demo_mode"] = int(demo_mode)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.db.session() as connection:
            rows = connection.execute(
                f"SELECT * FROM devices {where_clause} ORDER BY last_seen DESC, product_name ASC",
                params,
            ).fetchall()
        return [self._map(row) for row in rows]

    def get(self, device_key: str) -> USBDevice | None:
        with self.db.session() as connection:
            row = connection.execute("SELECT * FROM devices WHERE device_key = ?", (device_key,)).fetchone()
        return self._map(row) if row else None

    def find_reconnect_candidate(self, device: USBDevice, demo_mode: bool) -> USBDevice | None:
        matches = [candidate for candidate in self.list_all(demo_mode=demo_mode) if self._same_logical_device(candidate, device)]
        if not matches:
            return None

        connected = [candidate for candidate in matches if candidate.status == "connected"]
        if len(connected) == 1:
            return connected[0]
        if len(connected) > 1:
            return None

        matches.sort(key=lambda item: item.last_seen, reverse=True)
        return matches[0]

    def delete_disconnected_duplicates(self, keep_key: str, device: USBDevice, demo_mode: bool) -> None:
        duplicates = [
            candidate
            for candidate in self.list_all(demo_mode=demo_mode)
            if candidate.device_key != keep_key
            and candidate.status != "connected"
            and self._same_logical_device(candidate, device)
        ]
        if not duplicates:
            return

        with self.db.session() as connection:
            for duplicate in duplicates:
                connection.execute("DELETE FROM devices WHERE device_key = ?", (duplicate.device_key,))

    def counts(self, demo_mode: bool) -> dict[str, int]:
        with self.db.session() as connection:
            rows = connection.execute(
                """
                SELECT status, COUNT(*) AS total
                FROM devices
                WHERE demo_mode = ?
                GROUP BY status
                """,
                (int(demo_mode),),
            ).fetchall()
        result = {"connected": 0, "disconnected": 0}
        for row in rows:
            result[row["status"]] = row["total"]
        return result

    def _same_logical_device(self, left: USBDevice, right: USBDevice) -> bool:
        if left.vid != right.vid or left.pid != right.pid:
            return False

        if left.serial_number and right.serial_number:
            return left.serial_number.strip().upper() == right.serial_number.strip().upper()

        if left.serial_number or right.serial_number:
            return False

        if left.category != right.category:
            return False

        vendor_compatible = (
            _normalize_text(left.vendor_name) == _normalize_text(right.vendor_name)
            or _is_generic_vendor(left.vendor_name)
            or _is_generic_vendor(right.vendor_name)
        )
        product_compatible = (
            _normalize_text(left.product_name) == _normalize_text(right.product_name)
            or _is_generic_product(left.product_name)
            or _is_generic_product(right.product_name)
        )
        return vendor_compatible and product_compatible

    def _map(self, row) -> USBDevice:
        return USBDevice(
            device_key=row["device_key"],
            vid=row["vid"],
            pid=row["pid"],
            vendor_name=row["vendor_name"] or "Inconnu",
            product_name=row["product_name"] or "Périphérique USB",
            serial_number=row["serial_number"],
            usb_class=row["usb_class"],
            category=row["category"] or "unknown",
            bus=row["bus"],
            address=row["address"],
            first_seen=row["first_seen"] or "",
            last_seen=row["last_seen"] or "",
            status=row["status"] or "connected",
            risk_score=row["risk_score"] or 0,
            risk_level=row["risk_level"] or "LOW",
            confidence=row["confidence"] or 0.0,
            identification_source=row["identification_source"] or "unknown",
            source_backend=row["source_backend"] or "pyusb",
            metadata=_loads(row["metadata_json"], {}),
            demo_mode=bool(row["demo_mode"]),
        )


class EventRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def add(self, event: DeviceEvent) -> int:
        payload = asdict(event)
        payload["reasons_json"] = _dumps(payload.pop("reasons"))
        payload["payload_json"] = _dumps(payload.pop("payload"))
        payload["demo_mode"] = int(payload["demo_mode"])
        payload.pop("id", None)
        with self.db.session() as connection:
            cursor = connection.execute(
                """
                INSERT INTO device_events (
                    occurred_at, event_type, device_key, summary, severity, score,
                    level, reasons_json, source, payload_json, demo_mode
                ) VALUES (
                    :occurred_at, :event_type, :device_key, :summary, :severity, :score,
                    :level, :reasons_json, :source, :payload_json, :demo_mode
                )
                """,
                payload,
            )
        return int(cursor.lastrowid)

    def has_recent_duplicate(self, device_key: str | None, event_type: str, demo_mode: bool, since: str) -> bool:
        with self.db.session() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM device_events
                WHERE (
                    (device_key = ?)
                    OR
                    (device_key IS NULL AND ? IS NULL)
                )
                  AND event_type = ?
                  AND demo_mode = ?
                  AND occurred_at >= ?
                """,
                (device_key, device_key, event_type, int(demo_mode), since),
            ).fetchone()
        return bool(row["total"])

    def list_recent(
        self,
        *,
        limit: int = 200,
        search: str = "",
        severity: str = "",
        demo_mode: bool | None = None,
    ) -> list[DeviceEvent]:
        conditions = []
        params: dict[str, Any] = {"limit": limit}
        if search:
            conditions.append("(summary LIKE :search OR device_key LIKE :search)")
            params["search"] = f"%{search}%"
        if severity:
            conditions.append("severity = :severity")
            params["severity"] = severity
        if demo_mode is not None:
            conditions.append("demo_mode = :demo_mode")
            params["demo_mode"] = int(demo_mode)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.db.session() as connection:
            rows = connection.execute(
                f"SELECT * FROM device_events {where_clause} ORDER BY occurred_at DESC LIMIT :limit",
                params,
            ).fetchall()
        return [self._map(row) for row in rows]

    def list_device_events_since(self, device_key: str, since: str, demo_mode: bool) -> list[dict[str, Any]]:
        with self.db.session() as connection:
            rows = connection.execute(
                """
                SELECT occurred_at, event_type, severity, score
                FROM device_events
                WHERE device_key = ? AND demo_mode = ? AND occurred_at >= ?
                ORDER BY occurred_at DESC
                """,
                (device_key, int(demo_mode), since),
            ).fetchall()
        return [dict(row) for row in rows]

    def count_today(self, demo_mode: bool, since: str) -> int:
        with self.db.session() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM device_events
                WHERE demo_mode = ? AND occurred_at >= ?
                """,
                (int(demo_mode), since),
            ).fetchone()
        return int(row["total"])

    def cleanup(self, keep_since: str) -> None:
        with self.db.session() as connection:
            connection.execute("DELETE FROM device_events WHERE occurred_at < ?", (keep_since,))

    def _map(self, row) -> DeviceEvent:
        return DeviceEvent(
            id=row["id"],
            occurred_at=row["occurred_at"],
            event_type=row["event_type"],
            device_key=row["device_key"],
            summary=row["summary"],
            severity=row["severity"],
            score=row["score"] or 0,
            level=row["level"] or "LOW",
            reasons=_loads(row["reasons_json"], []),
            source=row["source"],
            payload=_loads(row["payload_json"], {}),
            demo_mode=bool(row["demo_mode"]),
        )


class PolicyRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def add(self, entry: PolicyEntry) -> int:
        payload = asdict(entry)
        payload["enabled"] = int(payload["enabled"])
        payload.pop("id", None)
        with self.db.session() as connection:
            connection.execute(
                """
                INSERT INTO policies (
                    policy_type, match_type, value, label, notes, enabled, created_at, updated_at
                ) VALUES (
                    :policy_type, :match_type, :value, :label, :notes, :enabled, :created_at, :updated_at
                )
                ON CONFLICT(policy_type, match_type, value) DO UPDATE SET
                    label = excluded.label,
                    notes = excluded.notes,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                payload,
            )
            row = connection.execute(
                """
                SELECT id
                FROM policies
                WHERE policy_type = ? AND match_type = ? AND value = ?
                """,
                (entry.policy_type, entry.match_type, entry.value),
            ).fetchone()
        return int(row["id"])

    def delete(self, entry_id: int) -> None:
        with self.db.session() as connection:
            connection.execute("DELETE FROM policies WHERE id = ?", (entry_id,))

    def list_all(self, policy_type: str = "", query: str = "") -> list[PolicyEntry]:
        conditions = []
        params: dict[str, Any] = {}
        if policy_type:
            conditions.append("policy_type = :policy_type")
            params["policy_type"] = policy_type
        if query:
            conditions.append("(value LIKE :query OR label LIKE :query OR notes LIKE :query)")
            params["query"] = f"%{query}%"
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.db.session() as connection:
            rows = connection.execute(
                f"SELECT * FROM policies {where_clause} ORDER BY policy_type, value",
                params,
            ).fetchall()
        return [self._map(row) for row in rows]

    def find_matching(self, vid_pid: str, serial_number: str | None) -> list[PolicyEntry]:
        with self.db.session() as connection:
            rows = connection.execute(
                """
                SELECT * FROM policies
                WHERE enabled = 1
                  AND (
                    (match_type = 'vid_pid' AND value = ?)
                    OR
                    (match_type = 'serial' AND value = ?)
                  )
                ORDER BY policy_type
                """,
                (vid_pid, serial_number or ""),
            ).fetchall()
        return [self._map(row) for row in rows]

    def _map(self, row) -> PolicyEntry:
        return PolicyEntry(
            id=row["id"],
            policy_type=row["policy_type"],
            match_type=row["match_type"],
            value=row["value"],
            label=row["label"] or "",
            notes=row["notes"] or "",
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class AlertRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def add(self, alert: Alert) -> int:
        payload = asdict(alert)
        payload["acknowledged"] = int(payload["acknowledged"])
        payload["recommendations_json"] = _dumps(payload.pop("recommendations"))
        payload["demo_mode"] = int(payload["demo_mode"])
        payload.pop("id", None)
        with self.db.session() as connection:
            cursor = connection.execute(
                """
                INSERT INTO alerts (
                    created_at, severity, title, message, device_key, event_id,
                    acknowledged, acknowledged_at, score, recommendations_json, demo_mode
                ) VALUES (
                    :created_at, :severity, :title, :message, :device_key, :event_id,
                    :acknowledged, :acknowledged_at, :score, :recommendations_json, :demo_mode
                )
                """,
                payload,
            )
        return int(cursor.lastrowid)

    def list_all(self, severity: str = "", acknowledged: str = "", demo_mode: bool | None = None) -> list[Alert]:
        conditions = []
        params: dict[str, Any] = {}
        if severity:
            conditions.append("severity = :severity")
            params["severity"] = severity
        if acknowledged:
            conditions.append("acknowledged = :acknowledged")
            params["acknowledged"] = 1 if acknowledged == "yes" else 0
        if demo_mode is not None:
            conditions.append("demo_mode = :demo_mode")
            params["demo_mode"] = int(demo_mode)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.db.session() as connection:
            rows = connection.execute(
                f"SELECT * FROM alerts {where_clause} ORDER BY created_at DESC",
                params,
            ).fetchall()
        return [self._map(row) for row in rows]

    def acknowledge(self, alert_id: int, acknowledged_at: str) -> None:
        with self.db.session() as connection:
            connection.execute(
                "UPDATE alerts SET acknowledged = 1, acknowledged_at = ? WHERE id = ?",
                (acknowledged_at, alert_id),
            )

    def counts(self, demo_mode: bool) -> dict[str, int]:
        with self.db.session() as connection:
            rows = connection.execute(
                """
                SELECT severity, COUNT(*) AS total
                FROM alerts
                WHERE demo_mode = ?
                GROUP BY severity
                """,
                (int(demo_mode),),
            ).fetchall()
        return {row["severity"]: row["total"] for row in rows}

    def cleanup(self, keep_since: str) -> None:
        with self.db.session() as connection:
            connection.execute("DELETE FROM alerts WHERE created_at < ?", (keep_since,))

    def _map(self, row) -> Alert:
        return Alert(
            id=row["id"],
            created_at=row["created_at"],
            severity=row["severity"],
            title=row["title"],
            message=row["message"],
            device_key=row["device_key"],
            event_id=row["event_id"],
            acknowledged=bool(row["acknowledged"]),
            acknowledged_at=row["acknowledged_at"],
            score=row["score"] or 0,
            recommendations=_loads(row["recommendations_json"], []),
            demo_mode=bool(row["demo_mode"]),
        )


class AssessmentRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def add(self, assessment: RiskAssessment) -> int:
        payload = asdict(assessment)
        payload["reasons_json"] = _dumps(payload.pop("reasons"))
        payload["recommendations_json"] = _dumps(payload.pop("recommendations"))
        payload["metadata_json"] = _dumps(payload.pop("metadata"))
        payload.pop("id", None)
        with self.db.session() as connection:
            cursor = connection.execute(
                """
                INSERT INTO risk_assessments (
                    assessed_at, device_key, score, level, reasons_json,
                    recommendations_json, profile_name, metadata_json
                ) VALUES (
                    :assessed_at, :device_key, :score, :level, :reasons_json,
                    :recommendations_json, :profile_name, :metadata_json
                )
                """,
                payload,
            )
        return int(cursor.lastrowid)

    def latest(self, device_key: str) -> RiskAssessment | None:
        with self.db.session() as connection:
            row = connection.execute(
                "SELECT * FROM risk_assessments WHERE device_key = ? ORDER BY assessed_at DESC LIMIT 1",
                (device_key,),
            ).fetchone()
        if not row:
            return None
        return RiskAssessment(
            id=row["id"],
            assessed_at=row["assessed_at"],
            device_key=row["device_key"],
            score=row["score"],
            level=row["level"],
            reasons=_loads(row["reasons_json"], []),
            recommendations=_loads(row["recommendations_json"], []),
            profile_name=row["profile_name"],
            metadata=_loads(row["metadata_json"], {}),
        )

    def cleanup(self, keep_since: str) -> None:
        with self.db.session() as connection:
            connection.execute("DELETE FROM risk_assessments WHERE assessed_at < ?", (keep_since,))


class SettingsRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def save(self, settings: AppSettings) -> None:
        with self.db.session() as connection:
            for key, value in settings.to_dict().items():
                connection.execute(
                    """
                    INSERT INTO settings(key, value_json)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json
                    """,
                    (key, _dumps(value)),
                )

    def load(self) -> dict[str, Any]:
        with self.db.session() as connection:
            rows = connection.execute("SELECT key, value_json FROM settings").fetchall()
        return {row["key"]: _loads(row["value_json"], None) for row in rows}


class HealthRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def replace_all(self, statuses: list[HealthStatus]) -> None:
        with self.db.session() as connection:
            for status in statuses:
                connection.execute(
                    """
                    INSERT INTO health_checks(component, status, details, checked_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(component) DO UPDATE SET
                        status = excluded.status,
                        details = excluded.details,
                        checked_at = excluded.checked_at
                    """,
                    (status.component, status.status, status.details, status.checked_at),
                )

    def list_all(self) -> list[HealthStatus]:
        with self.db.session() as connection:
            rows = connection.execute("SELECT * FROM health_checks ORDER BY component ASC").fetchall()
        return [
            HealthStatus(
                component=row["component"],
                status=row["status"],
                details=row["details"],
                checked_at=row["checked_at"],
            )
            for row in rows
        ]

    def get(self, component: str) -> HealthStatus | None:
        with self.db.session() as connection:
            row = connection.execute("SELECT * FROM health_checks WHERE component = ?", (component,)).fetchone()
        if row is None:
            return None
        return HealthStatus(
            component=row["component"],
            status=row["status"],
            details=row["details"],
            checked_at=row["checked_at"],
        )


class AIAnalysisRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def add(self, analysis: AIAnalysis) -> int:
        payload = asdict(analysis)
        payload["success"] = int(payload["success"])
        payload["threats_json"] = _dumps(payload.pop("threats"))
        payload["recommendations_json"] = _dumps(payload.pop("recommendations"))
        payload["context_json"] = _dumps(payload.pop("context"))
        payload.pop("id", None)
        with self.db.session() as connection:
            cursor = connection.execute(
                """
                INSERT INTO ai_analyses (
                    created_at, model, global_level, summary, threats_json,
                    recommendations_json, raw_response, success, context_json
                ) VALUES (
                    :created_at, :model, :global_level, :summary, :threats_json,
                    :recommendations_json, :raw_response, :success, :context_json
                )
                """,
                payload,
            )
        return int(cursor.lastrowid)

    def list_recent(self, limit: int = 10) -> list[AIAnalysis]:
        with self.db.session() as connection:
            rows = connection.execute(
                "SELECT * FROM ai_analyses ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            AIAnalysis(
                id=row["id"],
                created_at=row["created_at"],
                model=row["model"],
                global_level=row["global_level"],
                summary=row["summary"],
                threats=_loads(row["threats_json"], []),
                recommendations=_loads(row["recommendations_json"], []),
                raw_response=row["raw_response"],
                success=bool(row["success"]),
                context=_loads(row["context_json"], {}),
            )
            for row in rows
        ]

    def cleanup(self, keep_since: str) -> None:
        with self.db.session() as connection:
            connection.execute("DELETE FROM ai_analyses WHERE created_at < ?", (keep_since,))
