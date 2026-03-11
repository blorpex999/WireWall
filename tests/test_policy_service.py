from __future__ import annotations

from app.models.entities import USBDevice
from app.services.policy_service import PolicyService


def test_policy_service_add_evaluate_and_export_import(workspace_tmp_dir, repositories) -> None:
    service = PolicyService(repositories["policy_repo"], repositories["device_repo"])
    service.add_entry(
        policy_type="whitelist",
        match_type="vid_pid",
        value="1234:5678",
        label="Test device",
        notes="autorisé",
    )

    device = USBDevice(device_key="1234:5678:1", vid=0x1234, pid=0x5678)
    evaluation = service.evaluate_device(device)
    assert evaluation["is_whitelisted"] is True
    assert evaluation["is_blacklisted"] is False

    export_path = workspace_tmp_dir / "policies.json"
    service.export_entries(export_path)
    imported_repo_service = PolicyService(repositories["policy_repo"], repositories["device_repo"])
    count = imported_repo_service.import_entries(export_path)
    assert count == 1
