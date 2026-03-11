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
            raise FakeRequestException(f"HTTP {self.status_code}", response=self)


class FakeRequestException(Exception):
    def __init__(self, message: str, response=None) -> None:
        super().__init__(message)
        self.response = response


def test_ollama_service_success(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(*args, **kwargs):
        captured["json"] = kwargs.get("json")
        return FakeResponse(ok=True, payload={"response": "Niveau global HIGH\nAction: verifier le support"})

    fake_requests = SimpleNamespace(
        get=lambda *args, **kwargs: FakeResponse(ok=True, payload={"models": [{"name": "demo-model"}]}),
        post=fake_post,
        RequestException=FakeRequestException,
    )
    monkeypatch.setattr(ollama_module, "requests", fake_requests)
    service = OllamaService("http://127.0.0.1:11434", "demo-model", 3)

    health = service.health_check()
    analysis = service.analyze({"global_score": 60})

    assert health.status == "ok"
    assert analysis.success is True
    assert analysis.global_level == "HIGH"
    assert captured["json"]["options"]["num_predict"] == 180
    assert "Contexte JSON compact" in captured["json"]["prompt"]


def test_ollama_service_reports_missing_model_in_health(monkeypatch) -> None:
    fake_requests = SimpleNamespace(
        get=lambda *args, **kwargs: FakeResponse(ok=True, payload={"models": [{"name": "mistral:latest"}]}),
        post=lambda *args, **kwargs: FakeResponse(ok=True, payload={"response": "ok"}),
        RequestException=FakeRequestException,
    )
    monkeypatch.setattr(ollama_module, "requests", fake_requests)
    service = OllamaService("http://127.0.0.1:11434", "llama3.2:3b", 3)

    health = service.health_check()

    assert health.status == "warning"
    assert "llama3.2:3b" in health.details
    assert "mistral:latest" in health.details


def test_ollama_service_reports_missing_model_on_analysis(monkeypatch) -> None:
    missing_model_response = FakeResponse(
        ok=False,
        payload={"error": "model 'llama3.2:3b' not found"},
        status_code=404,
    )

    fake_requests = SimpleNamespace(
        get=lambda *args, **kwargs: FakeResponse(ok=True, payload={"models": [{"name": "mistral:latest"}]}),
        post=lambda *args, **kwargs: missing_model_response,
        RequestException=FakeRequestException,
    )
    monkeypatch.setattr(ollama_module, "requests", fake_requests)
    service = OllamaService("http://127.0.0.1:11434", "llama3.2:3b", 3)

    analysis = service.analyze({"global_score": 10})

    assert analysis.success is False
    assert "introuvable" in analysis.summary
    assert "ollama list" in " ".join(analysis.recommendations)


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
