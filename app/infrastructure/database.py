from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS devices (
        device_key TEXT PRIMARY KEY,
        vid INTEGER,
        pid INTEGER,
        vendor_name TEXT,
        product_name TEXT,
        serial_number TEXT,
        usb_class INTEGER,
        category TEXT,
        bus INTEGER,
        address INTEGER,
        first_seen TEXT,
        last_seen TEXT,
        status TEXT,
        risk_score INTEGER,
        risk_level TEXT,
        confidence REAL,
        identification_source TEXT,
        source_backend TEXT,
        metadata_json TEXT,
        demo_mode INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS device_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        occurred_at TEXT NOT NULL,
        event_type TEXT NOT NULL,
        device_key TEXT,
        summary TEXT NOT NULL,
        severity TEXT NOT NULL,
        score INTEGER NOT NULL DEFAULT 0,
        level TEXT NOT NULL DEFAULT 'LOW',
        reasons_json TEXT NOT NULL DEFAULT '[]',
        source TEXT NOT NULL,
        payload_json TEXT NOT NULL DEFAULT '{}',
        demo_mode INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_type TEXT NOT NULL,
        match_type TEXT NOT NULL,
        value TEXT NOT NULL,
        label TEXT,
        notes TEXT,
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(policy_type, match_type, value)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        severity TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        device_key TEXT,
        event_id INTEGER,
        acknowledged INTEGER NOT NULL DEFAULT 0,
        acknowledged_at TEXT,
        score INTEGER NOT NULL DEFAULT 0,
        recommendations_json TEXT NOT NULL DEFAULT '[]',
        demo_mode INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS risk_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessed_at TEXT NOT NULL,
        device_key TEXT NOT NULL,
        score INTEGER NOT NULL,
        level TEXT NOT NULL,
        reasons_json TEXT NOT NULL DEFAULT '[]',
        recommendations_json TEXT NOT NULL DEFAULT '[]',
        profile_name TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS health_checks (
        component TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        details TEXT NOT NULL,
        checked_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        model TEXT NOT NULL,
        global_level TEXT NOT NULL,
        summary TEXT NOT NULL,
        threats_json TEXT NOT NULL DEFAULT '[]',
        recommendations_json TEXT NOT NULL DEFAULT '[]',
        raw_response TEXT NOT NULL DEFAULT '',
        success INTEGER NOT NULL DEFAULT 0,
        context_json TEXT NOT NULL DEFAULT '{}'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS brain_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        global_score INTEGER NOT NULL DEFAULT 0,
        global_level TEXT NOT NULL DEFAULT 'LOW',
        progress_status TEXT NOT NULL DEFAULT 'LEARNING',
        summary TEXT NOT NULL DEFAULT '',
        incident_count INTEGER NOT NULL DEFAULT 0,
        open_alert_count INTEGER NOT NULL DEFAULT 0,
        monitored_device_count INTEGER NOT NULL DEFAULT 0,
        recommendations_json TEXT NOT NULL DEFAULT '[]',
        focus_areas_json TEXT NOT NULL DEFAULT '[]',
        metadata_json TEXT NOT NULL DEFAULT '{}',
        demo_mode INTEGER NOT NULL DEFAULT 0
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_device_events_occurred_at ON device_events(occurred_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_device_events_device_key ON device_events(device_key)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_assessments_device_key ON risk_assessments(device_key)",
    "CREATE INDEX IF NOT EXISTS idx_brain_snapshots_created_at ON brain_snapshots(created_at DESC)",
]


class DatabaseManager:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        with self.session() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            count = connection.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
            if count == 0:
                connection.execute("INSERT INTO schema_version(version) VALUES (1)")

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=10000")
        try:
            yield connection
            connection.commit()
        except sqlite3.Error as exc:
            connection.rollback()
            raise RuntimeError(f"Erreur SQLite sur {self.db_path}: {exc}") from exc
        finally:
            connection.close()

    def healthcheck(self) -> bool:
        with self.session() as connection:
            result = connection.execute("SELECT 1").fetchone()
        return bool(result)
