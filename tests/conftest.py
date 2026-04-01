from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from app.config.defaults import build_default_settings
from app.infrastructure.database import DatabaseManager
from app.infrastructure.repositories import (
    AIAnalysisRepository,
    AlertRepository,
    AssessmentRepository,
    BrainSnapshotRepository,
    DeviceRepository,
    EventRepository,
    HealthRepository,
    IncidentRepository,
    PolicyRepository,
    RecommendationRepository,
    ReportAuditRepository,
    RuntimeStateRepository,
    SettingsRepository,
)


@pytest.fixture()
def workspace_tmp_dir() -> Path:
    base_dir = Path.cwd() / "wirewall_test_artifacts"
    base_dir.mkdir(parents=True, exist_ok=True)
    target = base_dir / f"case-{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    yield target
    shutil.rmtree(target, ignore_errors=True)


@pytest.fixture()
def temp_db(workspace_tmp_dir: Path) -> DatabaseManager:
    db = DatabaseManager(workspace_tmp_dir / "wirewall_test.db")
    db.initialize()
    return db


@pytest.fixture()
def repositories(temp_db: DatabaseManager) -> dict[str, object]:
    return {
        "device_repo": DeviceRepository(temp_db),
        "event_repo": EventRepository(temp_db),
        "policy_repo": PolicyRepository(temp_db),
        "alert_repo": AlertRepository(temp_db),
        "incident_repo": IncidentRepository(temp_db),
        "recommendation_repo": RecommendationRepository(temp_db),
        "assessment_repo": AssessmentRepository(temp_db),
        "settings_repo": SettingsRepository(temp_db),
        "health_repo": HealthRepository(temp_db),
        "ai_repo": AIAnalysisRepository(temp_db),
        "brain_repo": BrainSnapshotRepository(temp_db),
        "report_audit_repo": ReportAuditRepository(temp_db),
        "runtime_state_repo": RuntimeStateRepository(temp_db),
    }


@pytest.fixture()
def default_settings():
    settings = build_default_settings()
    settings.mode = "demo"
    settings.export_directory = ""
    return settings


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(["wirewall-tests", "-platform", "offscreen"])
    yield app
