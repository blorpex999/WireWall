from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.models.entities import DeviceEvent, OperationResult, ReportAudit


class IntegrityVerificationService:
    def __init__(self, report_audit_repo, event_repo) -> None:
        self.report_audit_repo = report_audit_repo
        self.event_repo = event_repo

    def verify(self, demo_mode: bool, limit: int = 50) -> OperationResult:
        audits = self.report_audit_repo.list_recent(demo_mode, limit=limit)
        audits = list(reversed(audits))
        file_results = [self._verify_file(audit) for audit in audits]
        chain_results = self._verify_audit_chain(audits)
        event_chain_result = self._verify_latest_event_chain(demo_mode, audits)

        modified = [item for item in file_results if item["status"] == "modified"]
        missing = [item for item in file_results if item["status"] == "missing"]
        chain_errors = [item for item in chain_results if item["status"] == "error"]

        details = {
            "audit_count": len(audits),
            "files": file_results,
            "chain": chain_results,
            "event_chain": event_chain_result,
        }
        if modified or missing or chain_errors or event_chain_result["status"] == "error":
            return OperationResult(
                False,
                "integrity_failed",
                "Verification d'integrite en echec: export modifie, manquant ou chaine incoherente.",
                details,
            )
        if any(item["status"] == "partial" for item in chain_results) or event_chain_result["status"] == "partial":
            return OperationResult(
                True,
                "integrity_partial",
                "Integrite des fichiers OK; certaines anciennes preuves ne contiennent pas assez de contexte pour recalculer toute la chaine.",
                details,
            )
        return OperationResult(True, "integrity_ok", "Integrite des exports et de la chaine d'audit verifiee.", details)

    def _verify_file(self, audit: ReportAudit) -> dict[str, object]:
        path = Path(audit.file_path)
        if not path.exists():
            return {"id": audit.id, "path": audit.file_path, "status": "missing", "expected": audit.file_sha256}
        actual = self._hash_file(path)
        status = "ok" if actual == audit.file_sha256 else "modified"
        sidecar = path.with_suffix(path.suffix + ".sha256.txt")
        sidecar_ok = sidecar.exists() and audit.file_sha256 in sidecar.read_text(encoding="utf-8", errors="replace")
        return {
            "id": audit.id,
            "path": audit.file_path,
            "status": status,
            "expected": audit.file_sha256,
            "actual": actual,
            "sidecar_ok": sidecar_ok,
        }

    def _verify_audit_chain(self, audits: list[ReportAudit]) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        previous_chain = "GENESIS"
        for audit in audits:
            context_hash = audit.config_summary.get("context_hash")
            if not context_hash:
                results.append(
                    {
                        "id": audit.id,
                        "status": "partial",
                        "message": "Contexte d'audit absent sur cet ancien export.",
                    }
                )
                previous_chain = audit.chain_hash
                continue
            expected = self._hash_text(f"{previous_chain}|{audit.file_sha256}|{context_hash}|{audit.export_format}")
            status = "ok" if expected == audit.chain_hash else "error"
            results.append({"id": audit.id, "status": status, "expected": expected, "actual": audit.chain_hash})
            previous_chain = audit.chain_hash
        return results

    def _verify_latest_event_chain(self, demo_mode: bool, audits: list[ReportAudit]) -> dict[str, object]:
        latest = audits[-1] if audits else None
        if latest is None:
            return {"status": "partial", "message": "Aucun audit exporte pour ce mode."}
        expected_event_chain = latest.config_summary.get("event_chain_hash")
        if not expected_event_chain:
            return {"status": "partial", "message": "Le dernier audit ne stocke pas le hash de chaine des evenements."}

        events = self.event_repo.list_recent(limit=200, demo_mode=demo_mode)
        actual_event_chain = self._event_chain_hash(events)
        return {
            "status": "ok" if actual_event_chain == expected_event_chain else "error",
            "expected": expected_event_chain,
            "actual": actual_event_chain,
        }

    def _event_chain_hash(self, events: list[DeviceEvent]) -> str:
        chain = "GENESIS"
        for event in sorted(events, key=lambda item: item.occurred_at):
            event_payload = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
            chain = self._hash_text(f"{chain}|{event_payload}")
        return chain

    def _hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _hash_text(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
