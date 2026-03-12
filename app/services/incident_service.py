from __future__ import annotations

from app.models.entities import IncidentCase
from app.utils.datetime import utc_now


class IncidentService:
    def __init__(self, incident_repo, alert_repo, policy_service, device_repo, operator_name_getter) -> None:
        self.incident_repo = incident_repo
        self.alert_repo = alert_repo
        self.policy_service = policy_service
        self.device_repo = device_repo
        self.operator_name_getter = operator_name_getter

    def ensure_for_alert(self, alert_id: int, demo_mode: bool) -> IncidentCase:
        existing = self.incident_repo.get_by_alert(alert_id)
        if existing is not None:
            return existing

        alert = self.alert_repo.get(alert_id)
        if alert is None:
            raise ValueError("Alerte introuvable.")

        now = utc_now()
        case = IncidentCase(
            created_at=now,
            updated_at=now,
            device_key=alert.device_key,
            alert_id=alert_id,
            status="new",
            decision="none",
            comment="",
            resolution_reason="",
            operator_name=self._operator_name(),
            demo_mode=demo_mode,
        )
        case.id = self.incident_repo.add(case)
        self.alert_repo.attach_case(alert_id, case.id)
        return case

    def update_case(
        self,
        *,
        alert_id: int,
        demo_mode: bool,
        status: str,
        decision: str,
        comment: str,
        resolution_reason: str,
    ) -> IncidentCase:
        case = self.ensure_for_alert(alert_id, demo_mode)
        now = utc_now()
        case.updated_at = now
        case.status = status
        case.decision = decision
        case.comment = comment.strip()
        case.resolution_reason = resolution_reason.strip()
        case.operator_name = self._operator_name()
        case.closed_at = now if status in {"resolved", "false_positive"} else None
        self.incident_repo.save(case)
        self._apply_decision(case)
        self.alert_repo.update_workflow(
            alert_id,
            analyst_comment=case.comment,
            resolution_reason=case.resolution_reason,
            acknowledged=status in {"resolved", "false_positive"},
            acknowledged_at=now if status in {"resolved", "false_positive"} else None,
            case_id=case.id,
        )
        return case

    def list_open(self, demo_mode: bool) -> list[IncidentCase]:
        return [
            case
            for case in self.incident_repo.list_all(demo_mode=demo_mode)
            if case.status not in {"resolved", "false_positive"}
        ]

    def count_open(self, demo_mode: bool) -> int:
        return self.incident_repo.count_open(demo_mode)

    def get_by_alert(self, alert_id: int) -> IncidentCase | None:
        return self.incident_repo.get_by_alert(alert_id)

    def _apply_decision(self, case: IncidentCase) -> None:
        if not case.device_key:
            return
        device = self.device_repo.get(case.device_key)
        if device is None:
            return

        decision = case.decision
        if decision == "whitelist":
            value = device.serial_number if device.serial_number else device.vid_pid
            match_type = "serial" if device.serial_number else "vid_pid"
            self.policy_service.add_entry(
                policy_type="whitelist",
                match_type=match_type,
                value=value,
                label=device.display_name,
                notes="Ajoute depuis le workflow incident",
            )
            self.device_repo.update_decision(case.device_key, "whitelist")
        elif decision == "blacklist":
            value = device.serial_number if device.serial_number else device.vid_pid
            match_type = "serial" if device.serial_number else "vid_pid"
            self.policy_service.add_entry(
                policy_type="blacklist",
                match_type=match_type,
                value=value,
                label=device.display_name,
                notes="Ajoute depuis le workflow incident",
            )
            self.device_repo.update_decision(case.device_key, "blacklist")
        elif decision in {"ignore_temporary", "watch", "trusted"}:
            self.device_repo.update_decision(case.device_key, decision)

    def _operator_name(self) -> str:
        value = self.operator_name_getter().strip()
        return value or "Operateur local"
