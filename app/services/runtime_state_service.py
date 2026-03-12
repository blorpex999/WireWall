from __future__ import annotations

from app.models.entities import DeviceEvent
from app.utils.datetime import utc_now


class RuntimeStateService:
    def __init__(self, runtime_state_repo, event_repo) -> None:
        self.runtime_state_repo = runtime_state_repo
        self.event_repo = event_repo

    def startup(self, mode: str, demo_mode: bool) -> bool:
        now = utc_now()
        previous = self.runtime_state_repo.mark_startup(mode, now)
        if bool(previous.get("last_clean_exit", 1)):
            return False

        self.event_repo.add(
            DeviceEvent(
                occurred_at=now,
                event_type="runtime_resume",
                device_key=None,
                summary="Redemarrage apres fermeture non propre detecte.",
                severity="WARNING",
                score=0,
                level="LOW",
                reasons=["La session precedente ne s'est pas terminee proprement."],
                source="runtime",
                payload={
                    "previous_mode": previous.get("last_mode", "unknown"),
                    "last_startup_at": previous.get("last_startup_at"),
                    "last_shutdown_at": previous.get("last_shutdown_at"),
                },
                demo_mode=demo_mode,
            )
        )
        return True

    def shutdown(self) -> None:
        self.runtime_state_repo.mark_shutdown(utc_now())
