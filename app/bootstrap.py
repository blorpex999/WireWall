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
    IncidentRepository,
    PolicyRepository,
    RecommendationRepository,
    ReportAuditRepository,
    RuntimeStateRepository,
    SettingsRepository,
)
from app.models.entities import AppSettings, DeviceEvent
from app.services.autostart_service import AutostartService
from app.services.background_tasks import BackgroundTaskService
from app.services.baseline_service import BaselineService
from app.services.brain_service import BrainService
from app.services.demo_service import DemoDataService, DemoUsbEnumerator, ModeSwitchingUsbEnumerator
from app.services.demo_threat_marker import DemoThreatMarkerScanner
from app.services.event_bus import EventBus
from app.services.health_service import HealthCheckService
from app.services.incident_service import IncidentService
from app.services.integrity_service import IntegrityVerificationService
from app.services.ollama_service import OllamaService
from app.services.ollama_runtime_service import OllamaRuntimeService
from app.services.policy_service import PolicyService
from app.services.recommendation_service import RecommendationService
from app.services.report_service import ReportService
from app.services.retention_service import RetentionService
from app.services.runtime_state_service import RuntimeStateService
from app.services.usb_control_service import UsbControlService
from app.services.usb_enumerator import UsbEnumerator
from app.services.usb_monitor import UsbMonitorService
from app.utils.datetime import utc_now


def _normalize_mode(settings: AppSettings) -> None:
    settings.mode = str(settings.mode or "real").strip().lower()
    if settings.mode not in {"real", "demo"}:
        settings.mode = "real"


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
    incident_repo: IncidentRepository
    recommendation_repo: RecommendationRepository
    assessment_repo: AssessmentRepository
    settings_repo: SettingsRepository
    health_repo: HealthRepository
    ai_analysis_repo: AIAnalysisRepository
    brain_snapshot_repo: BrainSnapshotRepository
    report_audit_repo: ReportAuditRepository
    runtime_state_repo: RuntimeStateRepository
    background_tasks: BackgroundTaskService
    retention_service: RetentionService
    baseline_service: BaselineService
    brain_service: BrainService
    policy_service: PolicyService
    incident_service: IncidentService
    recommendation_service: RecommendationService
    autostart_service: AutostartService
    runtime_state_service: RuntimeStateService
    usb_control_service: UsbControlService
    ollama_service: OllamaService
    ollama_runtime_service: OllamaRuntimeService
    report_service: ReportService
    health_service: HealthCheckService
    integrity_service: IntegrityVerificationService
    usb_monitor: UsbMonitorService
    demo_data_service: DemoDataService

    def shutdown(self) -> None:
        self.usb_monitor.stop()
        self.runtime_state_service.shutdown()
        self.background_tasks.shutdown()
        self.ollama_runtime_service.stop()


def build_container(config_path: str | None = None) -> ApplicationContainer:
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
    _normalize_mode(settings)
    requested_mode = settings.mode
    settings.export_directory = settings.export_directory or str(paths.exports_dir)

    db_path = paths.demo_db_path if requested_mode == "demo" else paths.db_path
    db = DatabaseManager(db_path)
    db.initialize()

    settings_repo = SettingsRepository(db)
    persisted = settings_repo.load()
    if persisted:
        merged = settings.to_dict()
        merged.update(persisted)
        settings = AppSettings(**merged)
        config_loader.apply_profile_defaults(settings)
    _normalize_mode(settings)
    settings.mode = requested_mode
    settings.export_directory = settings.export_directory or str(paths.exports_dir)

    setup_logging(paths.logs_dir, settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info("Initialisation de WireWall en mode %s", settings.mode)

    settings_repo.save(settings)
    persisted_settings = AppSettings(**settings.to_dict())
    config_loader.save(persisted_settings)

    device_repo = DeviceRepository(db)
    event_repo = EventRepository(db)
    policy_repo = PolicyRepository(db)
    alert_repo = AlertRepository(db)
    incident_repo = IncidentRepository(db)
    recommendation_repo = RecommendationRepository(db)
    assessment_repo = AssessmentRepository(db)
    health_repo = HealthRepository(db)
    ai_analysis_repo = AIAnalysisRepository(db)
    brain_snapshot_repo = BrainSnapshotRepository(db)
    report_audit_repo = ReportAuditRepository(db)
    runtime_state_repo = RuntimeStateRepository(db)

    classifier = DeviceClassifier()
    real_enumerator = UsbEnumerator(classifier)
    demo_enumerator = DemoUsbEnumerator(classifier)
    enumerator = ModeSwitchingUsbEnumerator(settings, real_enumerator, demo_enumerator)
    demo_threat_marker_scanner = DemoThreatMarkerScanner()
    event_bus = EventBus()
    background_tasks = BackgroundTaskService(event_bus)
    baseline_service = BaselineService()
    policy_service = PolicyService(policy_repo, device_repo)
    demo_data_service = DemoDataService()
    autostart_service = AutostartService()
    usb_control_service = UsbControlService(RegistryManager())
    ollama_service = OllamaService(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    ollama_runtime_service = OllamaRuntimeService(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )
    incident_service = IncidentService(
        incident_repo=incident_repo,
        alert_repo=alert_repo,
        policy_service=policy_service,
        device_repo=device_repo,
        operator_name_getter=lambda: settings.author_name,
    )
    recommendation_service = RecommendationService(
        recommendation_repo=recommendation_repo,
        device_repo=device_repo,
        alert_repo=alert_repo,
        policy_service=policy_service,
        operator_name_getter=lambda: settings.author_name,
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
        incident_service=incident_service,
        recommendation_service=recommendation_service,
        report_audit_repo=report_audit_repo,
        settings_getter=lambda: settings,
    )
    brain_service = BrainService(
        device_repo=device_repo,
        event_repo=event_repo,
        alert_repo=alert_repo,
        health_repo=health_repo,
        ai_analysis_repo=ai_analysis_repo,
        brain_snapshot_repo=brain_snapshot_repo,
        incident_service=incident_service,
        recommendation_service=recommendation_service,
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
    integrity_service = IntegrityVerificationService(report_audit_repo, event_repo)
    retention_service = RetentionService(
        event_repo,
        alert_repo,
        assessment_repo,
        ai_analysis_repo,
        brain_snapshot_repo,
        recommendation_repo,
        report_audit_repo,
    )
    runtime_state_service = RuntimeStateService(runtime_state_repo, event_repo)
    usb_monitor = UsbMonitorService(
        enumerator=enumerator,
        device_repo=device_repo,
        event_repo=event_repo,
        assessment_repo=assessment_repo,
        alert_repo=alert_repo,
        policy_service=policy_service,
        risk_engine=RiskEngine(),
        baseline_service=baseline_service,
        incident_service=incident_service,
        event_bus=event_bus,
        settings=settings,
        demo_threat_marker_scanner=demo_threat_marker_scanner,
    )

    demo_mode = settings.mode == "demo"
    if demo_mode:
        demo_data_service.seed(policy_service, alert_repo, event_repo)

    retention_service.apply(settings.history_retention_days)
    runtime_recovered = runtime_state_service.startup(settings.mode, demo_mode)
    if settings.autostart_enabled and not demo_mode:
        result = autostart_service.apply(True)
        if not result.success:
            logger.warning("Activation du demarrage automatique impossible: %s", result.message)
            event_repo.add(
                DeviceEvent(
                    occurred_at=utc_now(),
                    event_type="autostart_warning",
                    device_key=None,
                    summary=result.message,
                    severity="WARNING",
                    score=0,
                    level="LOW",
                    reasons=["Le demarrage automatique n'a pas pu etre active automatiquement."],
                    source="bootstrap",
                    payload=result.details,
                    demo_mode=demo_mode,
                )
            )
            event_bus.publish("monitor_warning", {"message": result.message, "details": result.details})
    health_service.run_all(demo_mode)
    brain_service.refresh(demo_mode, settings.recommendation_mode)

    if runtime_recovered:
        logger.warning("Reprise detectee apres fermeture non propre.")
        event_bus.publish(
            "monitor_warning",
            {"message": "Une fermeture non propre a ete detectee sur la session precedente.", "details": {"recovered_at": utc_now()}},
        )

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
        incident_repo=incident_repo,
        recommendation_repo=recommendation_repo,
        assessment_repo=assessment_repo,
        settings_repo=settings_repo,
        health_repo=health_repo,
        ai_analysis_repo=ai_analysis_repo,
        brain_snapshot_repo=brain_snapshot_repo,
        report_audit_repo=report_audit_repo,
        runtime_state_repo=runtime_state_repo,
        background_tasks=background_tasks,
        retention_service=retention_service,
        baseline_service=baseline_service,
        brain_service=brain_service,
        policy_service=policy_service,
        incident_service=incident_service,
        recommendation_service=recommendation_service,
        autostart_service=autostart_service,
        runtime_state_service=runtime_state_service,
        usb_control_service=usb_control_service,
        ollama_service=ollama_service,
        ollama_runtime_service=ollama_runtime_service,
        report_service=report_service,
        health_service=health_service,
        integrity_service=integrity_service,
        usb_monitor=usb_monitor,
        demo_data_service=demo_data_service,
    )
