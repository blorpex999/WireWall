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
    def __init__(self) -> None:
        self.calls: list[bool] = []

    def health_check(self, demo_mode: bool = False) -> HealthStatus:
        self.calls.append(demo_mode)
        detail = "Mode demo: Ollama non interroge, analyse simulee." if demo_mode else "Ollama repond localement."
        return HealthStatus("ollama", "ok", detail, utc_now())


def test_health_service_persists_component_statuses(temp_db, repositories, workspace_tmp_dir) -> None:
    paths = build_app_paths(base_dir=workspace_tmp_dir)
    paths.ensure()
    fake_ollama = FakeOllamaService()
    service = HealthCheckService(
        db=temp_db,
        paths=paths,
        enumerator=FakeEnumerator(),
        usb_control_service=FakeUsbControlService(),
        ollama_service=fake_ollama,
        health_repo=repositories["health_repo"],
        exports_dir_getter=lambda: paths.exports_dir,
    )

    statuses = service.run_all()

    components = {status.component for status in statuses}
    assert components == {"usb_backend", "database", "admin", "usbstor", "ollama", "logs", "exports"}

    stored = repositories["health_repo"].list_all()
    assert len(stored) == 7
    assert any(status.component == "database" and status.status == "ok" for status in stored)
    assert fake_ollama.calls == [False]


def test_health_service_passes_demo_mode_to_ollama(temp_db, repositories, workspace_tmp_dir) -> None:
    paths = build_app_paths(base_dir=workspace_tmp_dir)
    paths.ensure()
    fake_ollama = FakeOllamaService()
    service = HealthCheckService(
        db=temp_db,
        paths=paths,
        enumerator=FakeEnumerator(),
        usb_control_service=FakeUsbControlService(),
        ollama_service=fake_ollama,
        health_repo=repositories["health_repo"],
        exports_dir_getter=lambda: paths.exports_dir,
    )

    statuses = service.run_all(demo_mode=True)

    assert fake_ollama.calls == [True]
    assert any(status.component == "ollama" and "analyse simulee" in status.details for status in statuses)
