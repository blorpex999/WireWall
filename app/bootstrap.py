from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.config.defaults import APP_NAME
from app.core.classifier import DeviceClassifier
from app.core.risk_engine import RiskEngine
from app.infrastructure.config_loader import ConfigLoader
from app.infrastructure.database import DatabaseManager
from app.infrastructure.logging_setup import setup_logging
from app.infrastructure.paths import AppPaths, build_app_paths
from app.infrastructure.registry import RegistryManager
from app.infrastructure.repositories import (
    AIAnalysisRepository,
    AlertRepository,
    AssessmentRepository,
    BrainSnapshotRepository,
    DeviceRepository,
    EventRepository,
    HealthRepository,
    PolicyRepository,
    SettingsRepository,
)
from app.models.entities import AppSettings
from app.services.demo_service import DemoDataService, DemoUsbEnumerator
from app.services.background_tasks import BackgroundTaskService
from app.services.brain_service import BrainService
from app.services.event_bus import EventBus
from app.services.health_service import HealthCheckService
from app.services.ollama_service import OllamaService
from app.services.policy_service import PolicyService
from app.services.report_service import ReportService
from app.services.retention_service import RetentionService
from app.services.usb_control_service import UsbControlService
from app.services.usb_enumerator import UsbEnumerator
from app.services.usb_monitor import UsbMonitorService


@dataclass(slots=True)
class ApplicationContainer:
    paths: AppPaths
    settings: AppSettings
    config_loader: ConfigLoader
    db: DatabaseManager
    event_bus: EventBus
    device_repo: DeviceRepository
    event_repo: EventRepository
    policy_repo: PolicyRepository
    alert_repo: AlertRepository
    assessment_repo: AssessmentRepository
    settings_repo: SettingsRepository
    health_repo: HealthRepository
    ai_analysis_repo: AIAnalysisRepository
    brain_snapshot_repo: BrainSnapshotRepository
    background_tasks: BackgroundTaskService
    retention_service: RetentionService
    brain_service: BrainService
    policy_service: PolicyService
    usb_control_service: UsbControlService
    ollama_service: OllamaService
    report_service: ReportService
    health_service: HealthCheckService
    usb_monitor: UsbMonitorService

    def shutdown(self) -> None:
        self.usb_monitor.stop()
        self.background_tasks.shutdown()


def build_container(config_path: str | None = None, force_demo: bool = False) -> ApplicationContainer:
    paths = build_app_paths(APP_NAME)
    try:
        paths.ensure()
    except PermissionError:
        portable_root = Path.cwd() / ".wirewall-runtime"
        paths = build_app_paths(APP_NAME, base_dir=portable_root)
        paths.ensure()
    config_file = Path(config_path) if config_path else paths.config_file
    config_loader = ConfigLoader(config_file)
    settings = config_loader.load()
    configured_mode = settings.mode
    if force_demo:
        settings.mode = "demo"
    settings.export_directory = settings.export_directory or str(paths.exports_dir)

    db_path = paths.demo_db_path if settings.mode == "demo" else paths.db_path
    db = DatabaseManager(db_path)
    db.initialize()

    settings_repo = SettingsRepository(db)
    persisted = settings_repo.load()
    if persisted:
        merged = settings.to_dict()
        merged.update(persisted)
        settings = AppSettings(**merged)
        config_loader.apply_profile_defaults(settings)
    if force_demo:
        settings.mode = "demo"
    settings.export_directory = settings.export_directory or str(paths.exports_dir)

    setup_logging(paths.logs_dir, settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info("Initialisation de WireWall en mode %s", settings.mode)

    settings_repo.save(settings)
    persisted_settings = AppSettings(**settings.to_dict())
    if force_demo:
        persisted_settings.mode = configured_mode
    config_loader.save(persisted_settings)

    device_repo = DeviceRepository(db)
    event_repo = EventRepository(db)
    policy_repo = PolicyRepository(db)
    alert_repo = AlertRepository(db)
    assessment_repo = AssessmentRepository(db)
    health_repo = HealthRepository(db)
    ai_analysis_repo = AIAnalysisRepository(db)
    brain_snapshot_repo = BrainSnapshotRepository(db)

    classifier = DeviceClassifier()
    enumerator = DemoUsbEnumerator(classifier) if settings.mode == "demo" else UsbEnumerator(classifier)
    event_bus = EventBus()
    background_tasks = BackgroundTaskService(event_bus)
    policy_service = PolicyService(policy_repo, device_repo)
    usb_control_service = UsbControlService(RegistryManager())
    ollama_service = OllamaService(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    report_service = ReportService(
        exports_dir=Path(settings.export_directory),
        device_repo=device_repo,
        event_repo=event_repo,
        policy_service=policy_service,
        alert_repo=alert_repo,
        health_repo=health_repo,
        ai_analysis_repo=ai_analysis_repo,
        brain_snapshot_repo=brain_snapshot_repo,
    )
    brain_service = BrainService(
        device_repo=device_repo,
        event_repo=event_repo,
        alert_repo=alert_repo,
        health_repo=health_repo,
        ai_analysis_repo=ai_analysis_repo,
        brain_snapshot_repo=brain_snapshot_repo,
    )
    health_service = HealthCheckService(
        db=db,
        paths=paths,
        enumerator=enumerator,
        usb_control_service=usb_control_service,
        ollama_service=ollama_service,
        health_repo=health_repo,
        exports_dir_getter=lambda: report_service.exports_dir,
    )
    retention_service = RetentionService(event_repo, alert_repo, assessment_repo, ai_analysis_repo, brain_snapshot_repo)
    usb_monitor = UsbMonitorService(
        enumerator=enumerator,
        device_repo=device_repo,
        event_repo=event_repo,
        assessment_repo=assessment_repo,
        alert_repo=alert_repo,
        policy_service=policy_service,
        risk_engine=RiskEngine(),
        event_bus=event_bus,
        settings=settings,
    )

    retention_service.apply(settings.history_retention_days)
    if settings.mode == "demo":
        DemoDataService().seed(policy_service, alert_repo, event_repo)
    brain_service.refresh(settings.mode == "demo")

    return ApplicationContainer(
        paths=paths,
        settings=settings,
        config_loader=config_loader,
        db=db,
        event_bus=event_bus,
        device_repo=device_repo,
        event_repo=event_repo,
        policy_repo=policy_repo,
        alert_repo=alert_repo,
        assessment_repo=assessment_repo,
        settings_repo=settings_repo,
        health_repo=health_repo,
        ai_analysis_repo=ai_analysis_repo,
        brain_snapshot_repo=brain_snapshot_repo,
        background_tasks=background_tasks,
        retention_service=retention_service,
        brain_service=brain_service,
        policy_service=policy_service,
        usb_control_service=usb_control_service,
        ollama_service=ollama_service,
        report_service=report_service,
        health_service=health_service,
        usb_monitor=usb_monitor,
    )
