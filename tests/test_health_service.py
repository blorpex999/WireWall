from __future__ import annotations

from app.infrastructure.paths import build_app_paths
from app.models.entities import HealthStatus, OperationResult
from app.services.health_service import HealthCheckService
from app.utils.datetime import utc_now


class FakeEnumerator:
    def backend_status(self) -> tuple[bool, str]:
        return True, "Backend libusb1 charge."


class FakeUsbControlService:
    def get_status(self) -> OperationResult:
        return OperationResult(
            True,
            "allowed",
            "Stockage USB autorise.",
            {"registry_value": 3},
        )


class FakeOllamaService:
    def health_check(self) -> HealthStatus:
        return HealthStatus("ollama", "ok", "Ollama repond localement.", utc_now())


def test_health_service_persists_component_statuses(temp_db, repositories, workspace_tmp_dir) -> None:
    paths = build_app_paths(base_dir=workspace_tmp_dir)
    paths.ensure()
    service = HealthCheckService(
        db=temp_db,
        paths=paths,
        enumerator=FakeEnumerator(),
        usb_control_service=FakeUsbControlService(),
        ollama_service=FakeOllamaService(),
        health_repo=repositories["health_repo"],
        exports_dir_getter=lambda: paths.exports_dir,
    )

    statuses = service.run_all()

    components = {status.component for status in statuses}
    assert components == {"usb_backend", "database", "admin", "usbstor", "ollama", "logs", "exports"}

    stored = repositories["health_repo"].list_all()
    assert len(stored) == 7
    assert any(status.component == "database" and status.status == "ok" for status in stored)
