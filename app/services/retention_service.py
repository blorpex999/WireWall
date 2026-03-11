from __future__ import annotations

from app.utils.datetime import days_ago


class RetentionService:
    def __init__(self, event_repo, alert_repo, assessment_repo, ai_analysis_repo, brain_snapshot_repo) -> None:
        self.event_repo = event_repo
        self.alert_repo = alert_repo
        self.assessment_repo = assessment_repo
        self.ai_analysis_repo = ai_analysis_repo
        self.brain_snapshot_repo = brain_snapshot_repo

    def apply(self, retention_days: int) -> str:
        keep_since = days_ago(retention_days)
        self.event_repo.cleanup(keep_since)
        self.alert_repo.cleanup(keep_since)
        self.assessment_repo.cleanup(keep_since)
        self.ai_analysis_repo.cleanup(keep_since)
        self.brain_snapshot_repo.cleanup(keep_since)
        return keep_since
