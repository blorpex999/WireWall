from __future__ import annotations

from pathlib import Path

from app.models.entities import AIAnalysis, Alert, DeviceEvent, HealthStatus, RiskAssessment, USBDevice
from app.services.policy_service import PolicyService
from app.services.report_service import ReportService
from app.services.retention_service import RetentionService
from app.utils.datetime import days_ago, hours_ago, utc_now


def test_report_service_escapes_html(workspace_tmp_dir, repositories) -> None:
    device_repo = repositories["device_repo"]
    event_repo = repositories["event_repo"]
    alert_repo = repositories["alert_repo"]
    health_repo = repositories["health_repo"]
    ai_repo = repositories["ai_repo"]
    policy_service = PolicyService(repositories["policy_repo"], device_repo)

    device_repo.upsert(
        USBDevice(
            device_key="1234:5678:XSS",
            vid=0x1234,
            pid=0x5678,
            vendor_name="<script>alert(1)</script>",
            product_name="Mass Storage",
            serial_number="XSS",
            category="storage",
            first_seen=utc_now(),
            last_seen=utc_now(),
        )
    )
    event_repo.add(
        DeviceEvent(
            occurred_at=utc_now(),
            event_type="connected",
            device_key="1234:5678:XSS",
            summary="<b>connected</b>",
            severity="HIGH",
            source="test",
        )
    )
    alert_repo.add(
        Alert(
            created_at=utc_now(),
            severity="HIGH",
            title="<script>boom</script>",
            message='Device said "hello" <unsafe>',
        )
    )
    health_repo.replace_all([HealthStatus("ollama", "warning", "<offline>", utc_now())])
    ai_repo.add(
        AIAnalysis(
            created_at=utc_now(),
            model="demo",
            global_level="LOW",
            summary="ok",
            success=True,
        )
    )

    service = ReportService(
        exports_dir=workspace_tmp_dir,
        device_repo=device_repo,
        event_repo=event_repo,
        policy_service=policy_service,
        alert_repo=alert_repo,
        health_repo=health_repo,
        ai_analysis_repo=ai_repo,
    )
    target = service.export_html(False, str(workspace_tmp_dir / "report.html"))
    content = target.read_text(encoding="utf-8")

    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in content
    assert "&lt;script&gt;boom&lt;/script&gt;" in content
    assert "&lt;offline&gt;" in content
    assert "<script>alert(1)</script>" not in content
    assert "<script>boom</script>" not in content


def test_retention_service_cleans_multiple_tables(temp_db, repositories) -> None:
    old_timestamp = days_ago(40)
    recent_timestamp = utc_now()

    repositories["event_repo"].add(
        DeviceEvent(
            occurred_at=old_timestamp,
            event_type="connected",
            device_key="old-device",
            summary="old event",
            severity="LOW",
            source="test",
        )
    )
    repositories["event_repo"].add(
        DeviceEvent(
            occurred_at=recent_timestamp,
            event_type="connected",
            device_key="recent-device",
            summary="recent event",
            severity="LOW",
            source="test",
        )
    )
    repositories["alert_repo"].add(
        Alert(created_at=old_timestamp, severity="LOW", title="old alert", message="old")
    )
    repositories["alert_repo"].add(
        Alert(created_at=recent_timestamp, severity="LOW", title="recent alert", message="recent")
    )
    repositories["assessment_repo"].add(
        RiskAssessment(
            assessed_at=old_timestamp,
            device_key="old-device",
            score=10,
            level="LOW",
            profile_name="Normal",
        )
    )
    repositories["assessment_repo"].add(
        RiskAssessment(
            assessed_at=recent_timestamp,
            device_key="recent-device",
            score=20,
            level="LOW",
            profile_name="Normal",
        )
    )
    repositories["ai_repo"].add(
        AIAnalysis(
            created_at=old_timestamp,
            model="demo",
            global_level="LOW",
            summary="old analysis",
            success=False,
        )
    )
    repositories["ai_repo"].add(
        AIAnalysis(
            created_at=recent_timestamp,
            model="demo",
            global_level="LOW",
            summary="recent analysis",
            success=True,
        )
    )

    service = RetentionService(
        repositories["event_repo"],
        repositories["alert_repo"],
        repositories["assessment_repo"],
        repositories["ai_repo"],
    )
    keep_since = service.apply(30)

    assert keep_since <= recent_timestamp
    with temp_db.session() as connection:
        event_count = connection.execute("SELECT COUNT(*) AS total FROM device_events").fetchone()["total"]
        alert_count = connection.execute("SELECT COUNT(*) AS total FROM alerts").fetchone()["total"]
        assessment_count = connection.execute("SELECT COUNT(*) AS total FROM risk_assessments").fetchone()["total"]
        ai_count = connection.execute("SELECT COUNT(*) AS total FROM ai_analyses").fetchone()["total"]

    assert event_count == 1
    assert alert_count == 1
    assert assessment_count == 1
    assert ai_count == 1


def test_event_repository_count_today_uses_given_cutoff(repositories) -> None:
    repositories["event_repo"].add(
        DeviceEvent(
            occurred_at=days_ago(2),
            event_type="connected",
            device_key="old-device",
            summary="old event",
            severity="LOW",
            source="test",
        )
    )
    repositories["event_repo"].add(
        DeviceEvent(
            occurred_at=utc_now(),
            event_type="connected",
            device_key="recent-device",
            summary="recent event",
            severity="LOW",
            source="test",
        )
    )

    assert repositories["event_repo"].count_today(False, hours_ago(24)) == 1
