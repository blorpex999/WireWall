from __future__ import annotations

import csv
import json
from pathlib import Path

from app.models.entities import PolicyEntry, USBDevice
from app.utils.datetime import utc_now
from app.utils.validation import is_valid_vid_pid, normalize_serial, normalize_vid_pid


class PolicyService:
    def __init__(self, policy_repo, device_repo) -> None:
        self.policy_repo = policy_repo
        self.device_repo = device_repo

    def add_entry(
        self,
        *,
        policy_type: str,
        match_type: str,
        value: str,
        label: str = "",
        notes: str = "",
    ) -> int:
        normalized_value = self._normalize(match_type, value)
        now = utc_now()
        entry = PolicyEntry(
            policy_type=policy_type,
            match_type=match_type,
            value=normalized_value,
            label=label,
            notes=notes,
            enabled=True,
            created_at=now,
            updated_at=now,
        )
        return self.policy_repo.add(entry)

    def remove_entry(self, entry_id: int) -> None:
        self.policy_repo.delete(entry_id)

    def list_entries(self, policy_type: str = "", query: str = "") -> list[PolicyEntry]:
        return self.policy_repo.list_all(policy_type=policy_type, query=query)

    def evaluate_device(self, device: USBDevice) -> dict[str, object]:
        matches = self.policy_repo.find_matching(device.vid_pid, device.serial_number)
        policy_types = {entry.policy_type for entry in matches}
        known_device = self.device_repo.get(device.device_key) is not None
        return {
            "matches": matches,
            "is_whitelisted": "whitelist" in policy_types,
            "is_blacklisted": "blacklist" in policy_types,
            "is_known_device": known_device,
        }

    def export_entries(self, path: Path) -> Path:
        entries = self.list_entries()
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".json":
            path.write_text(
                json.dumps([entry.to_dict() for entry in entries], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return path
        if path.suffix.lower() != ".csv":
            raise ValueError("Le format d'export policy doit être .json ou .csv.")

        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["id", "policy_type", "match_type", "value", "label", "notes", "enabled", "created_at", "updated_at"],
            )
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry.to_dict())
        return path

    def import_entries(self, path: Path) -> int:
        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable: {path}")
        count = 0
        if path.suffix.lower() == ".json":
            try:
                items = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Fichier JSON invalide: {path}") from exc
            for item in items:
                self.add_entry(
                    policy_type=item["policy_type"],
                    match_type=item["match_type"],
                    value=item["value"],
                    label=item.get("label", ""),
                    notes=item.get("notes", ""),
                )
                count += 1
            return count
        if path.suffix.lower() != ".csv":
            raise ValueError("Le format d'import policy doit être .json ou .csv.")

        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                self.add_entry(
                    policy_type=row["policy_type"],
                    match_type=row["match_type"],
                    value=row["value"],
                    label=row.get("label", ""),
                    notes=row.get("notes", ""),
                )
                count += 1
        return count

    def _normalize(self, match_type: str, value: str) -> str:
        if match_type == "vid_pid":
            normalized = normalize_vid_pid(value)
            if not is_valid_vid_pid(normalized):
                raise ValueError("Le format VID:PID doit respecter AAAA:BBBB.")
            return normalized
        if match_type == "serial":
            return normalize_serial(value)
        raise ValueError("Type de correspondance de policy non supporté.")
