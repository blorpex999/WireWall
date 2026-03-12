from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class USBDevice:
    device_key: str
    vid: int | None
    pid: int | None
    vendor_name: str = "Inconnu"
    product_name: str = "Périphérique USB"
    serial_number: str | None = None
    usb_class: int | None = None
    category: str = "unknown"
    bus: int | None = None
    address: int | None = None
    first_seen: str = ""
    last_seen: str = ""
    status: str = "connected"
    risk_score: int = 0
    risk_level: str = "LOW"
    confidence: float = 0.5
    identification_source: str = "unknown"
    source_backend: str = "pyusb"
    metadata: dict[str, Any] = field(default_factory=dict)
    seen_count: int = 0
    usual_hours: dict[str, int] = field(default_factory=dict)
    trust_state: str = "NEW"
    last_decision: str = ""
    recent_variation: str = "stable"
    demo_mode: bool = False

    @property
    def display_name(self) -> str:
        label = f"{self.vendor_name} {self.product_name}".strip()
        return label if label else "Périphérique USB"

    @property
    def vid_pid(self) -> str:
        vid = "????" if self.vid is None else f"{self.vid:04X}"
        pid = "????" if self.pid is None else f"{self.pid:04X}"
        return f"{vid}:{pid}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DeviceEvent:
    occurred_at: str
    event_type: str
    device_key: str | None
    summary: str
    severity: str
    score: int = 0
    level: str = "LOW"
    reasons: list[str] = field(default_factory=list)
    source: str = "monitor"
    payload: dict[str, Any] = field(default_factory=dict)
    demo_mode: bool = False
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PolicyEntry:
    policy_type: str
    match_type: str
    value: str
    label: str = ""
    notes: str = ""
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Alert:
    created_at: str
    severity: str
    title: str
    message: str
    device_key: str | None = None
    event_id: int | None = None
    case_id: int | None = None
    acknowledged: bool = False
    acknowledged_at: str | None = None
    score: int = 0
    recommendations: list[str] = field(default_factory=list)
    analyst_comment: str = ""
    resolution_reason: str = ""
    demo_mode: bool = False
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RiskAssessment:
    assessed_at: str
    device_key: str
    score: int
    level: str
    reasons: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    profile_name: str = "Normal"
    metadata: dict[str, Any] = field(default_factory=dict)
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AppSettings:
    app_name: str
    mode: str
    scan_interval_seconds: int
    history_retention_days: int
    log_level: str
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: int
    security_profile: str
    theme: str
    export_directory: str
    alert_threshold: int
    dedup_window_seconds: int
    dashboard_refresh_ms: int
    autostart_enabled: bool = False
    desktop_notifications_enabled: bool = True
    recommendation_mode: str = "balanced"
    author_name: str = ""
    organization_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AIAnalysis:
    created_at: str
    model: str
    global_level: str
    summary: str
    threats: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    raw_response: str = ""
    success: bool = False
    context: dict[str, Any] = field(default_factory=dict)
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BrainSnapshot:
    created_at: str
    global_score: int
    global_level: str
    progress_status: str
    summary: str
    incident_count: int = 0
    open_alert_count: int = 0
    monitored_device_count: int = 0
    open_incident_count: int = 0
    suggestion_count: int = 0
    new_device_count: int = 0
    deviation_count: int = 0
    recommendations: list[str] = field(default_factory=list)
    focus_areas: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    demo_mode: bool = False
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class HealthStatus:
    component: str
    status: str
    details: str
    checked_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class OperationResult:
    success: bool
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EnumerationResult:
    success: bool
    devices: list[USBDevice] = field(default_factory=list)
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IncidentCase:
    created_at: str
    updated_at: str
    device_key: str | None
    alert_id: int | None = None
    status: str = "new"
    decision: str = "none"
    comment: str = ""
    resolution_reason: str = ""
    operator_name: str = ""
    closed_at: str | None = None
    demo_mode: bool = False
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RecommendationEntry:
    stable_key: str
    created_at: str
    updated_at: str
    recommendation_type: str
    priority: str
    title: str
    details: str
    proposed_action: str
    target_device_key: str | None = None
    target_alert_id: int | None = None
    status: str = "pending"
    operator_comment: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    demo_mode: bool = False
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReportAudit:
    created_at: str
    export_format: str
    file_path: str
    file_sha256: str
    chain_hash: str
    config_summary: dict[str, Any] = field(default_factory=dict)
    demo_mode: bool = False
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
