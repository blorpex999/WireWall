from __future__ import annotations

from types import SimpleNamespace

from app.services import ollama_service as ollama_module
from app.services.ollama_service import OllamaService


class FakeResponse:
    def __init__(self, ok: bool = True, payload: dict | None = None, status_code: int = 200) -> None:
        self.ok = ok
        self._payload = payload or {}
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not self.ok:
            raise FakeRequestException(f"HTTP {self.status_code}")


class FakeRequestException(Exception):
    pass


def test_ollama_service_success(monkeypatch) -> None:
    fake_requests = SimpleNamespace(
        get=lambda *args, **kwargs: FakeResponse(ok=True),
        post=lambda *args, **kwargs: FakeResponse(ok=True, payload={"response": "Niveau global HIGH\nAction: vérifier le support"}),
        RequestException=FakeRequestException,
    )
    monkeypatch.setattr(ollama_module, "requests", fake_requests)
    service = OllamaService("http://127.0.0.1:11434", "demo-model", 3)
    analysis = service.analyze({"global_score": 60})
    assert analysis.success is True
    assert analysis.global_level == "HIGH"


def test_ollama_service_failure(monkeypatch) -> None:
    def failing_post(*args, **kwargs):
        raise FakeRequestException("offline")

    fake_requests = SimpleNamespace(
        get=lambda *args, **kwargs: FakeResponse(ok=False, status_code=500),
        post=failing_post,
        RequestException=FakeRequestException,
    )
    monkeypatch.setattr(ollama_module, "requests", fake_requests)
    service = OllamaService("http://127.0.0.1:11434", "demo-model", 3)
    analysis = service.analyze({"global_score": 10})
    assert analysis.success is False
    assert "offline" in analysis.summary
