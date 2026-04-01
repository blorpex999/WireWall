from __future__ import annotations

from app.models.entities import OperationResult
from app.services import ollama_runtime_service as runtime_module
from app.services.ollama_runtime_service import OllamaRuntimeService


class FakeProcess:
    def __init__(self, pid: int = 4242) -> None:
        self.pid = pid
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self.returncode = 1

    def wait(self, timeout: float | None = None) -> int | None:
        return self.returncode


def test_ollama_runtime_service_reuses_existing_local_api(monkeypatch) -> None:
    service = OllamaRuntimeService("http://127.0.0.1:11434", "qwen2.5:14b")
    monkeypatch.setattr(service, "_api_responds", lambda: True)

    result = service.ensure_started()

    assert result.success is True
    assert result.status == "running"
    assert result.details["managed"] is False


def test_ollama_runtime_service_starts_and_stops_managed_process(monkeypatch) -> None:
    service = OllamaRuntimeService("http://127.0.0.1:11434", "qwen2.5:14b")
    fake_process = FakeProcess()
    captured: dict[str, object] = {}

    monkeypatch.setattr(service, "_api_responds", lambda: False)
    monkeypatch.setattr(service, "_wait_until_ready", lambda: True)
    monkeypatch.setattr(runtime_module.shutil, "which", lambda name: r"C:\Ollama\ollama.exe")

    def fake_popen(args, **kwargs):
        captured["args"] = args
        captured["env"] = kwargs["env"]
        return fake_process

    monkeypatch.setattr(runtime_module.subprocess, "Popen", fake_popen)

    start_result = service.ensure_started()
    stop_result = service.stop()

    assert start_result.success is True
    assert start_result.status == "started"
    assert captured["args"] == [r"C:\Ollama\ollama.exe", "serve"]
    assert captured["env"]["OLLAMA_HOST"] == "127.0.0.1:11434"
    assert stop_result.success is True
    assert fake_process.terminated is True


def test_ollama_runtime_service_reports_missing_executable(monkeypatch) -> None:
    service = OllamaRuntimeService("http://127.0.0.1:11434", "qwen2.5:14b")
    monkeypatch.setattr(service, "_api_responds", lambda: False)
    monkeypatch.setattr(runtime_module.shutil, "which", lambda name: None)

    result = service.ensure_started()

    assert result.success is False
    assert result.status == "missing"


def test_ollama_runtime_service_update_restarts_only_managed_process(monkeypatch) -> None:
    service = OllamaRuntimeService("http://127.0.0.1:11434", "qwen2.5:14b")
    service._managed_process = FakeProcess()
    calls: list[str] = []

    monkeypatch.setattr(
        service,
        "stop",
        lambda: calls.append("stop") or OperationResult(True, "stopped", "ok"),
    )
    monkeypatch.setattr(
        service,
        "ensure_started",
        lambda: calls.append("start") or OperationResult(True, "started", "ok"),
    )

    result = service.update(base_url="http://localhost:11434", model="qwen2.5:14b")

    assert result is not None
    assert calls == ["stop", "start"]
