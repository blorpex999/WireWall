from __future__ import annotations

from app.utils.datetime import days_ago


class RetentionService:
    def __init__(
        self,
        event_repo,
        alert_repo,
        assessment_repo,
        ai_analysis_repo,
        brain_snapshot_repo,
        recommendation_repo=None,
        report_audit_repo=None,
    ) -> None:
        self.event_repo = event_repo
        self.alert_repo = alert_repo
        self.assessment_repo = assessment_repo
        self.ai_analysis_repo = ai_analysis_repo
        self.brain_snapshot_repo = brain_snapshot_repo
        self.recommendation_repo = recommendation_repo
        self.report_audit_repo = report_audit_repo

    def apply(self, retention_days: int) -> str:
        keep_since = days_ago(retention_days)
        self.event_repo.cleanup(keep_since)
        self.alert_repo.cleanup(keep_since)
        self.assessment_repo.cleanup(keep_since)
        self.ai_analysis_repo.cleanup(keep_since)
        self.brain_snapshot_repo.cleanup(keep_since)
        if self.recommendation_repo is not None:
            self.recommendation_repo.cleanup(keep_since)
        if self.report_audit_repo is not None:
            self.report_audit_repo.cleanup(keep_since)
        return keep_since
