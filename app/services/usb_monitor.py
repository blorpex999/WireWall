from __future__ import annotations

import logging
import threading

from app.models.entities import Alert, DeviceEvent, USBDevice
from app.utils.datetime import minutes_ago, seconds_ago, utc_now

LOGGER = logging.getLogger(__name__)

GENERIC_VENDOR_NAMES = {"", "INCONNU", "UNKNOWN"}
GENERIC_PRODUCT_NAMES = {
    "",
    "P\u00c9RIPH\u00c9RIQUE USB",
    "PERIPHERIQUE USB",
    "USB DEVICE",
    "UNKNOWN",
}


class UsbMonitorService:
    def __init__(
        self,
        enumerator,
        device_repo,
        event_repo,
        assessment_repo,
        alert_repo,
        policy_service,
        risk_engine,
        baseline_service,
        incident_service,
        event_bus,
        settings,
        demo_threat_marker_scanner=None,
    ) -> None:
        self.enumerator = enumerator
        self.device_repo = device_repo
        self.event_repo = event_repo
        self.assessment_repo = assessment_repo
        self.alert_repo = alert_repo
        self.policy_service = policy_service
        self.risk_engine = risk_engine
        self.baseline_service = baseline_service
        self.incident_service = incident_service
        self.event_bus = event_bus
        self.settings = settings
        self.demo_threat_marker_scanner = demo_threat_marker_scanner
        self._current_snapshot: dict[str, USBDevice] = {}
        self._stop_event = threading.Event()
        self._refresh_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def demo_mode(self) -> bool:
        return self.settings.mode == "demo"

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="wirewall-usb-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._refresh_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def refresh_now(self) -> None:
        self._refresh_event.set()

    def update_settings(self, settings) -> None:
        previous_demo_mode = self.demo_mode
        self.settings = settings
        if previous_demo_mode != self.demo_mode:
            self._current_snapshot = {}
        self.refresh_now()

    def _run(self) -> None:
        import time

        _last_scan: float = 0.0
        _MIN_SCAN_INTERVAL = 0.5

        while not self._stop_event.is_set():
            try:
                now = time.monotonic()
                if now - _last_scan >= _MIN_SCAN_INTERVAL:
                    self.scan_once()
                    _last_scan = time.monotonic()
            except Exception as exc:
                LOGGER.exception("Erreur non g\u00e9r\u00e9e dans la boucle de monitoring USB.")
                self.event_bus.publish("monitor_error", {"message": f"Erreur de monitoring USB: {exc}"})
            self._refresh_event.wait(timeout=max(1, self.settings.scan_interval_seconds))
            self._refresh_event.clear()

    def scan_once(self) -> bool:
        enumeration = self.enumerator.enumerate()
        if not enumeration.success:
            LOGGER.warning("Scan USB ignor\u00e9: %s", enumeration.message)
            self._create_system_event(
                event_type="scan_error",
                summary=enumeration.message,
                severity="WARNING",
                reasons=[enumeration.message],
            )
            self.event_bus.publish("monitor_warning", {"message": enumeration.message, "details": enumeration.details})
            return False

        devices = enumeration.devices
        now = utc_now()
        new_snapshot: dict[str, USBDevice] = {}
        for device in devices:
            canonical = self._canonicalize_device(device, set(new_snapshot))
            new_snapshot[canonical.device_key] = canonical
        previous_snapshot = self._current_snapshot

        for device in new_snapshot.values():
            existing = self.device_repo.get(device.device_key)
            connected_transition = existing is None or existing.status != "connected"
            device.first_seen = existing.first_seen if existing and existing.first_seen else now
            device.last_seen = now
            device.status = "connected"
            self._device_assessment(device, existing, connected_transition, now)

        for key, previous_device in previous_snapshot.items():
            if key not in new_snapshot:
                disconnected = previous_device
                disconnected.last_seen = now
                disconnected.status = "disconnected"
                self.device_repo.upsert(disconnected)
                self._create_event(
                    event_type="disconnected",
                    device=disconnected,
                    summary=f"{disconnected.display_name} d\u00e9connect\u00e9.",
                    level=disconnected.risk_level,
                    score=disconnected.risk_score,
                    reasons=["Le p\u00e9riph\u00e9rique n'est plus d\u00e9tect\u00e9 dans le snapshot courant."],
                )

        self._current_snapshot = new_snapshot
        self._scan_demo_threat_markers(now)
        self.event_bus.publish("snapshot_updated", {"device_count": len(new_snapshot)})
        return True

    def _canonicalize_device(self, device: USBDevice, reserved_keys: set[str]) -> USBDevice:
        candidate = self.device_repo.find_reconnect_candidate(device, self.demo_mode)
        if candidate is None or candidate.device_key in reserved_keys:
            return device

        device.device_key = candidate.device_key
        if candidate.first_seen:
            device.first_seen = candidate.first_seen
        if self._is_generic_vendor(device.vendor_name) and not self._is_generic_vendor(candidate.vendor_name):
            device.vendor_name = candidate.vendor_name
        if self._is_generic_product(device.product_name) and not self._is_generic_product(candidate.product_name):
            device.product_name = candidate.product_name
        if not device.serial_number and candidate.serial_number:
            device.serial_number = candidate.serial_number
        if device.confidence < candidate.confidence and (
            self._is_generic_vendor(device.vendor_name) or self._is_generic_product(device.product_name)
        ):
            device.confidence = candidate.confidence
            device.identification_source = candidate.identification_source
        if candidate.seen_count:
            device.seen_count = candidate.seen_count
            device.usual_hours = dict(candidate.usual_hours)
            device.trust_state = candidate.trust_state
            device.last_decision = candidate.last_decision
            device.recent_variation = candidate.recent_variation
        self.device_repo.delete_disconnected_duplicates(device.device_key, device, self.demo_mode)
        return device

    def _device_assessment(self, device: USBDevice, existing: USBDevice | None, connected_transition: bool, now: str) -> None:
        baseline = self.baseline_service.update_device(
            device=device,
            existing=existing,
            connected_transition=connected_transition,
            now=now,
        )
        policies = self.policy_service.evaluate_device(device)
        policies["baseline"] = baseline
        recent_events = self.event_repo.list_device_events_since(device.device_key, minutes_ago(10), self.demo_mode)
        assessment = self.risk_engine.assess(device, recent_events, policies, self.settings.security_profile, now)
        device.risk_score = assessment.score
        device.risk_level = assessment.level
        self.device_repo.upsert(device)
        self.assessment_repo.add(assessment)

        if connected_transition:
            event_id = self._create_event(
                event_type="connected",
                device=device,
                summary=f"{device.display_name} connect\u00e9.",
                level=assessment.level,
                score=assessment.score,
                reasons=assessment.reasons,
            )
            if assessment.score >= self.settings.alert_threshold:
                alert = Alert(
                    created_at=now,
                    severity=assessment.level,
                    title=f"Alerte USB {assessment.level}",
                    message=f"{device.display_name} pr\u00e9sente un score de risque de {assessment.score}.",
                    device_key=device.device_key,
                    event_id=event_id,
                    score=assessment.score,
                    recommendations=assessment.recommendations,
                    demo_mode=self.demo_mode,
                )
                alert.id = self.alert_repo.add(alert)
                if alert.id is not None:
                    case = self.incident_service.ensure_for_alert(alert.id, self.demo_mode)
                    self.alert_repo.attach_case(alert.id, case.id or 0)
                    self.event_bus.publish(
                        "alert_created",
                        {
                            "alert_id": alert.id,
                            "severity": alert.severity,
                            "title": alert.title,
                            "message": alert.message,
                            "device_key": alert.device_key,
                        },
                    )

    def _scan_demo_threat_markers(self, now: str) -> None:
        if self.demo_threat_marker_scanner is None:
            return
        try:
            markers = self.demo_threat_marker_scanner.scan()
        except Exception:
            LOGGER.exception("Erreur pendant le scan des marqueurs de simulation USB.")
            return
        if not markers:
            return

        marker = markers[0]
        event_id = self._create_system_event(
            event_type="usb_attack_simulation_marker_detected",
            summary=f"Marqueur de simulation d'attaque USB detecte sur {marker.drive_root}.",
            severity="HIGH",
            reasons=[
                "Un fichier marqueur de demonstration WireWall est present a la racine du support.",
                "Aucun programme n'a ete execute: il s'agit d'un scenario controle.",
            ],
            score=85,
            level="HIGH",
            payload={
                "drive_root": marker.drive_root,
                "marker_name": marker.marker_name,
                "marker_path": marker.marker_path,
            },
        )
        if event_id is None:
            return

        alert = Alert(
            created_at=now,
            severity="HIGH",
            title="Simulation d'attaque USB",
            message=f"Marqueur de scenario suspect detecte sur {marker.drive_root}.",
            event_id=event_id,
            score=85,
            recommendations=[
                "Presenter ce support comme un scenario controle, sans malware reel.",
                "Ouvrir un incident et documenter la decision analyste.",
                "Retirer le support apres la demonstration.",
            ],
            demo_mode=self.demo_mode,
        )
        alert.id = self.alert_repo.add(alert)
        if alert.id is not None:
            case = self.incident_service.ensure_for_alert(alert.id, self.demo_mode)
            self.alert_repo.attach_case(alert.id, case.id or 0)
            self.event_bus.publish(
                "alert_created",
                {
                    "alert_id": alert.id,
                    "severity": alert.severity,
                    "title": alert.title,
                    "message": alert.message,
                    "device_key": None,
                },
            )

    def _create_event(
        self,
        *,
        event_type: str,
        device: USBDevice,
        summary: str,
        level: str,
        score: int,
        reasons: list[str],
    ) -> int | None:
        since = seconds_ago(self.settings.dedup_window_seconds)
        if self.event_repo.has_recent_duplicate(device.device_key, event_type, self.demo_mode, since):
            return None
        event = DeviceEvent(
            occurred_at=utc_now(),
            event_type=event_type,
            device_key=device.device_key,
            summary=summary,
            severity=level,
            score=score,
            level=level,
            reasons=reasons,
            source="monitor",
            payload={
                "vid_pid": device.vid_pid,
                "category": device.category,
                "trust_state": device.trust_state,
                "seen_count": device.seen_count,
            },
            demo_mode=self.demo_mode,
        )
        event_id = self.event_repo.add(event)
        self.event_bus.publish("device_event", {"event_id": event_id, "device_key": device.device_key})
        return event_id

    def _create_system_event(
        self,
        *,
        event_type: str,
        summary: str,
        severity: str,
        reasons: list[str],
        score: int = 0,
        level: str = "LOW",
        payload: dict | None = None,
    ) -> int | None:
        since = seconds_ago(self.settings.dedup_window_seconds)
        if self.event_repo.has_recent_duplicate(None, event_type, self.demo_mode, since):
            return None
        event_id = self.event_repo.add(
            DeviceEvent(
                occurred_at=utc_now(),
                event_type=event_type,
                device_key=None,
                summary=summary,
                severity=severity,
                score=score,
                level=level,
                reasons=reasons,
                source="monitor",
                payload=payload or {},
                demo_mode=self.demo_mode,
            )
        )
        self.event_bus.publish("device_event", {"event_id": event_id, "device_key": None})
        return event_id

    def _is_generic_vendor(self, value: str | None) -> bool:
        return (value or "").strip().upper() in GENERIC_VENDOR_NAMES

    def _is_generic_product(self, value: str | None) -> bool:
        return (value or "").strip().upper() in GENERIC_PRODUCT_NAMES
