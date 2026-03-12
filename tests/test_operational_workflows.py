from __future__ import annotations

from app.models.entities import Alert, USBDevice
from app.services.baseline_service import BaselineService
from app.services.incident_service import IncidentService
from app.services.policy_service import PolicyService
from app.services.recommendation_service import RecommendationService
from app.utils.datetime import utc_now


def test_baseline_service_marks_known_then_deviation() -> None:
    service = BaselineService()
    existing = USBDevice(
        device_key="046D:C539",
        vid=0x046D,
        pid=0xC539,
        vendor_name="Logitech",
        product_name="USB Receiver",
        category="hid",
        seen_count=4,
        usual_hours={"9": 4, "10": 2, "11": 1},
        trust_state="KNOWN",
        first_seen=utc_now(),
        last_seen=utc_now(),
    )

    known = USBDevice(
        device_key="046D:C539",
        vid=0x046D,
        pid=0xC539,
        vendor_name="Logitech",
        product_name="USB Receiver",
        category="hid",
    )
    baseline_known = service.update_device(
        device=known,
        existing=existing,
        connected_transition=True,
        now="2026-03-12T09:15:00+00:00",
    )
    assert baseline_known["trust_state"] == "KNOWN"
    assert baseline_known["outside_habit"] is False
    assert baseline_known["seen_count"] == 5

    deviating = USBDevice(
        device_key="046D:C539",
        vid=0x046D,
        pid=0xC539,
        vendor_name="Logitech",
        product_name="USB Receiver",
        category="hid",
    )
    baseline_deviation = service.update_device(
        device=deviating,
        existing=existing,
        connected_transition=True,
        now="2026-03-12T22:15:00+00:00",
    )
    assert baseline_deviation["trust_state"] == "DEVIATION"
    assert baseline_deviation["outside_habit"] is True
    assert deviating.recent_variation == "deviation"


def test_incident_workflow_links_alert_and_applies_whitelist(repositories) -> None:
    policy_service = PolicyService(repositories["policy_repo"], repositories["device_repo"])
    incident_service = IncidentService(
        incident_repo=repositories["incident_repo"],
        alert_repo=repositories["alert_repo"],
        policy_service=policy_service,
        device_repo=repositories["device_repo"],
        operator_name_getter=lambda: "Analyste Demo",
    )
    device = USBDevice(
        device_key="046D:C539",
        vid=0x046D,
        pid=0xC539,
        vendor_name="Logitech",
        product_name="USB Receiver",
        category="hid",
        first_seen=utc_now(),
        last_seen=utc_now(),
    )
    repositories["device_repo"].upsert(device)
    alert_id = repositories["alert_repo"].add(
        Alert(
            created_at=utc_now(),
            severity="HIGH",
            title="Receiver inconnu",
            message="Le receiver a ete reconnecte hors plage habituelle.",
            device_key=device.device_key,
        )
    )

    case = incident_service.ensure_for_alert(alert_id, demo_mode=False)
    updated_case = incident_service.update_case(
        alert_id=alert_id,
        demo_mode=False,
        status="resolved",
        decision="whitelist",
        comment="Receiver confirme comme legitime",
        resolution_reason="Validation analyste",
    )
    updated_alert = repositories["alert_repo"].get(alert_id)
    stored_device = repositories["device_repo"].get(device.device_key)
    whitelist_entries = repositories["policy_repo"].list_all(policy_type="whitelist")

    assert case.id is not None
    assert updated_case.status == "resolved"
    assert updated_alert is not None and updated_alert.acknowledged is True
    assert stored_device is not None and stored_device.last_decision == "whitelist"
    assert any(entry.value == device.vid_pid for entry in whitelist_entries)


def test_recommendation_service_generates_and_applies_supervised_actions(repositories) -> None:
    policy_service = PolicyService(repositories["policy_repo"], repositories["device_repo"])
    service = RecommendationService(
        recommendation_repo=repositories["recommendation_repo"],
        device_repo=repositories["device_repo"],
        alert_repo=repositories["alert_repo"],
        policy_service=policy_service,
        operator_name_getter=lambda: "Analyste Demo",
    )
    trusted_receiver = USBDevice(
        device_key="046D:C539",
        vid=0x046D,
        pid=0xC539,
        vendor_name="Logitech",
        product_name="USB Receiver",
        category="hid",
        status="connected",
        risk_score=12,
        risk_level="LOW",
        seen_count=6,
        trust_state="KNOWN",
        first_seen=utc_now(),
        last_seen=utc_now(),
    )
    suspicious_storage = USBDevice(
        device_key="1234:5678:SUS",
        vid=0x1234,
        pid=0x5678,
        vendor_name="Unknown",
        product_name="Mass Storage",
        category="storage",
        status="connected",
        risk_score=81,
        risk_level="HIGH",
        seen_count=1,
        trust_state="NEW",
        first_seen=utc_now(),
        last_seen=utc_now(),
    )
    repositories["device_repo"].upsert(trusted_receiver)
    repositories["device_repo"].upsert(suspicious_storage)

    suggestions = service.refresh(demo_mode=False, mode="balanced")
    stable_keys = {entry.stable_key for entry in suggestions}

    assert f"whitelist:{trusted_receiver.device_key}" in stable_keys
    assert f"blacklist:{suspicious_storage.device_key}" in stable_keys

    blacklist_recommendation = next(
        entry for entry in suggestions if entry.stable_key == f"blacklist:{suspicious_storage.device_key}"
    )
    assert repositories["policy_repo"].list_all(policy_type="blacklist") == []

    accepted = service.accept(blacklist_recommendation.id or 0)
    blacklist_entries = repositories["policy_repo"].list_all(policy_type="blacklist")

    assert accepted.status == "accepted"
    assert any(entry.value == suspicious_storage.vid_pid for entry in blacklist_entries)
