from __future__ import annotations

import time
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


def test_ollama_service_success_parses_strict_json(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(*args, **kwargs):
        captured["json"] = kwargs.get("json")
        return FakeResponse(
            ok=True,
            payload={
                "response": (
                    '{"niveau":"HIGH","resume":"Risque eleve sur support USB inconnu.","menaces":["Support inconnu","Alerte recente"],'
                    '"actions":["Verifier le support","Confirmer l utilisateur"]}'
                )
            },
        )

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
    assert analysis.summary == "Risque eleve sur support USB inconnu."
    assert analysis.threats == ["Support inconnu", "Alerte recente"]
    assert analysis.recommendations == ["Verifier le support", "Confirmer l utilisateur"]
    assert captured["json"]["options"]["num_predict"] == 180
    assert '"niveau":"LOW | MEDIUM | HIGH | CRITICAL"' in captured["json"]["prompt"]
    assert "aucun markdown" in captured["json"]["prompt"]


def test_ollama_service_extracts_json_from_wrapped_text(monkeypatch) -> None:
    fake_requests = SimpleNamespace(
        get=lambda *args, **kwargs: FakeResponse(ok=True, payload={"models": [{"name": "demo-model"}]}),
        post=lambda *args, **kwargs: FakeResponse(
            ok=True,
            payload={
                "response": 'Analyse:\n{"niveau":"LOW","resume":"Situation calme.","menaces":[],"actions":["Continuer la surveillance"]}\nFin'
            },
        ),
        RequestException=FakeRequestException,
    )
    monkeypatch.setattr(ollama_module, "requests", fake_requests)
    service = OllamaService("http://127.0.0.1:11434", "demo-model", 3)

    analysis = service.analyze({"global_score": 10})

    assert analysis.success is True
    assert analysis.global_level == "LOW"
    assert analysis.recommendations == ["Continuer la surveillance"]


def test_ollama_service_invalid_json_returns_clean_fallback(monkeypatch) -> None:
    fake_requests = SimpleNamespace(
        get=lambda *args, **kwargs: FakeResponse(ok=True, payload={"models": [{"name": "demo-model"}]}),
        post=lambda *args, **kwargs: FakeResponse(ok=True, payload={"response": "pas de json exploitable"}),
        RequestException=FakeRequestException,
    )
    monkeypatch.setattr(ollama_module, "requests", fake_requests)
    service = OllamaService("http://127.0.0.1:11434", "demo-model", 3)

    analysis = service.analyze({"global_score": 10})

    assert analysis.success is False
    assert analysis.global_level == "UNKNOWN"
    assert "reponse invalide du modele" in analysis.summary


def test_ollama_service_demo_mode_never_calls_network(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("Aucun appel reseau ne doit etre effectue en mode demo.")

    monkeypatch.setattr(
        ollama_module,
        "requests",
        SimpleNamespace(get=fail, post=fail, RequestException=FakeRequestException),
    )
    service = OllamaService("http://127.0.0.1:11434", "qwen2.5:14b", 60)

    health = service.health_check(demo_mode=True)
    analysis = service.analyze(
        {
            "global_score": 62,
            "summary": {"alert_total": 2, "device_total": 3},
            "alerts": [
                {"severity": "HIGH", "title": "Cle inconnue", "message": "Support branche"},
                {"severity": "MEDIUM", "title": "Deviation", "message": "Horaire inhabituel"},
            ],
        },
        demo_mode=True,
    )

    assert health.status == "ok"
    assert "analyse simulee" in health.details
    assert analysis.success is True
    assert analysis.global_level == "HIGH"
    assert len(analysis.threats) == 2
    assert len(analysis.recommendations) == 2


def test_ollama_service_rejects_non_local_base_url(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("Aucun appel reseau ne doit etre effectue pour une URL Ollama distante.")

    monkeypatch.setattr(
        ollama_module,
        "requests",
        SimpleNamespace(get=fail, post=fail, RequestException=FakeRequestException),
    )
    service = OllamaService("https://example.com:11434", "qwen2.5:14b", 60)

    health = service.health_check()
    analysis = service.analyze({"global_score": 20})

    assert health.status == "warning"
    assert "locale" in health.details.lower()
    assert analysis.success is False
    assert "url ollama doit rester locale" in analysis.summary.lower()


def test_ollama_service_timeout_returns_clean_error(monkeypatch) -> None:
    def slow_post(*args, **kwargs):
        time.sleep(0.05)
        return FakeResponse(ok=True, payload={"response": '{"niveau":"LOW","resume":"ok","menaces":[],"actions":[]}'} )

    fake_requests = SimpleNamespace(
        get=lambda *args, **kwargs: FakeResponse(ok=True, payload={"models": [{"name": "demo-model"}]}),
        post=slow_post,
        RequestException=FakeRequestException,
    )
    monkeypatch.setattr(ollama_module, "requests", fake_requests)
    service = OllamaService("http://127.0.0.1:11434", "demo-model", 0.01)

    analysis = service.analyze({"global_score": 10})

    assert analysis.success is False
    assert "timeout ollama" in analysis.summary.lower()


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
