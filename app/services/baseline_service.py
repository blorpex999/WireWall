from __future__ import annotations

from app.models.entities import USBDevice
from app.utils.datetime import parse_timestamp


class BaselineService:
    def update_device(
        self,
        *,
        device: USBDevice,
        existing: USBDevice | None,
        connected_transition: bool,
        now: str,
    ) -> dict[str, object]:
        hour = self._current_hour(now)
        usual_hours = dict(existing.usual_hours) if existing else {}
        seen_count = existing.seen_count if existing else 0
        last_decision = existing.last_decision if existing else ""

        if connected_transition:
            seen_count += 1
            usual_hours[str(hour)] = int(usual_hours.get(str(hour), 0)) + 1

        outside_habit = self._is_outside_habit(hour, usual_hours, seen_count)
        trust_state = self._compute_trust_state(seen_count, outside_habit)
        recent_variation = "deviation" if outside_habit else "stable"

        device.seen_count = seen_count
        device.usual_hours = usual_hours
        device.trust_state = trust_state
        device.last_decision = last_decision or device.last_decision
        device.recent_variation = recent_variation

        return {
            "seen_count": seen_count,
            "trust_state": trust_state,
            "outside_habit": outside_habit,
            "usual_hours": usual_hours,
            "recent_variation": recent_variation,
            "habit_label": self.habit_label(seen_count),
        }

    def habit_label(self, seen_count: int) -> str:
        if seen_count <= 1:
            return "Nouveau"
        if seen_count <= 3:
            return "Rare"
        return "Habituel"

    def _current_hour(self, now: str) -> int:
        parsed = parse_timestamp(now)
        if parsed is None:
            return 0
        return parsed.astimezone().hour

    def _is_outside_habit(self, hour: int, usual_hours: dict[str, int], seen_count: int) -> bool:
        if seen_count < 4 or not usual_hours:
            return False
        dominant_hours = sorted(usual_hours.items(), key=lambda item: item[1], reverse=True)[:3]
        return str(hour) not in {hour_key for hour_key, _count in dominant_hours}

    def _compute_trust_state(self, seen_count: int, outside_habit: bool) -> str:
        if seen_count <= 1:
            return "NEW"
        if outside_habit:
            return "DEVIATION"
        if seen_count <= 3:
            return "RARE"
        return "KNOWN"
