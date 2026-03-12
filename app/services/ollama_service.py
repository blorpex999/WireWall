from __future__ import annotations

import json
from typing import Any

from app.models.entities import AIAnalysis, HealthStatus
from app.utils.datetime import utc_now

try:
    import requests
except ImportError:  # pragma: no cover - optional during tests
    requests = None


class OllamaService:
    def __init__(self, base_url: str, model: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def update(self, *, base_url: str, model: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def health_check(self) -> HealthStatus:
        if requests is None:
            return HealthStatus("ollama", "error", "La dependance requests est indisponible.", utc_now())
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=min(self.timeout_seconds, 3))
            response.raise_for_status()
            payload = response.json()
            model_names = self._extract_model_names(payload)
            if not model_names:
                return HealthStatus(
                    "ollama",
                    "warning",
                    "Ollama repond localement, mais aucun modele installe n'a ete detecte.",
                    utc_now(),
                )
            if self.model not in model_names:
                return HealthStatus(
                    "ollama",
                    "warning",
                    f"Service Ollama disponible, mais le modele configure '{self.model}' est absent. Modeles installes: {', '.join(model_names[:5])}.",
                    utc_now(),
                )
            return HealthStatus("ollama", "ok", f"Ollama repond localement avec le modele '{self.model}'.", utc_now())
        except requests.RequestException as exc:
            return HealthStatus("ollama", "warning", f"Ollama indisponible: {exc}", utc_now())
        except ValueError as exc:
            return HealthStatus("ollama", "warning", f"Reponse Ollama invalide: {exc}", utc_now())

    def analyze(self, context: dict[str, Any]) -> AIAnalysis:
        if requests is None:
            return AIAnalysis(
                created_at=utc_now(),
                model=self.model,
                global_level="UNKNOWN",
                summary="Analyse IA impossible: dependance requests absente.",
                recommendations=["Installer les dependances runtime avant d'utiliser l'analyse IA."],
                raw_response="",
                success=False,
                context=context,
            )

        prompt = self._build_prompt(context)
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 180,
                    },
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            raw_text = data.get("response", "").strip()
            if not raw_text:
                return AIAnalysis(
                    created_at=utc_now(),
                    model=self.model,
                    global_level="UNKNOWN",
                    summary="Ollama n'a pas retourne de contenu exploitable.",
                    recommendations=["Verifier le modele local et reessayer l'analyse."],
                    raw_response=json.dumps(data, ensure_ascii=False),
                    success=False,
                    context=context,
                )
            summary = raw_text
            level = self._extract_level(summary, context)
            threats = self._extract_bullets(summary, prefix="Menace")
            recommendations = self._extract_bullets(summary, prefix="Action")
            if not recommendations:
                recommendations = ["Verifier les peripheriques actifs et les alertes avant validation utilisateur."]
            return AIAnalysis(
                created_at=utc_now(),
                model=self.model,
                global_level=level,
                summary=summary,
                threats=threats,
                recommendations=recommendations,
                raw_response=json.dumps(data, ensure_ascii=False),
                success=True,
                context=context,
            )
        except requests.RequestException as exc:
            detail = self._build_error_detail(exc)
            return AIAnalysis(
                created_at=utc_now(),
                model=self.model,
                global_level="UNKNOWN",
                summary=detail,
                recommendations=self._build_error_recommendations(exc),
                raw_response="",
                success=False,
                context=context,
            )
        except ValueError as exc:
            return AIAnalysis(
                created_at=utc_now(),
                model=self.model,
                global_level="UNKNOWN",
                summary=f"Analyse IA indisponible: reponse Ollama invalide ({exc}).",
                recommendations=["Verifier que le service Ollama local est demarre et que le modele repond correctement."],
                raw_response="",
                success=False,
                context=context,
            )

    def _build_prompt(self, context: dict[str, Any]) -> str:
        return (
            "Tu es un analyste cybersecurite local pour une application Windows de surveillance USB.\n"
            "Analyse le contexte ci-dessous et reponds en francais.\n"
            "Donne exactement quatre sections courtes dans cet ordre :\n"
            "Resume:\n"
            "Anomalies:\n"
            "Niveau global:\n"
            "Recommandations:\n"
            "Contraintes:\n"
            "- maximum 130 mots au total\n"
            "- niveau global parmi LOW, MEDIUM, HIGH ou CRITICAL\n"
            "- deux anomalies maximum\n"
            "- recommandations concretes, fiables et courtes\n"
            "- si le contexte est calme, dis-le clairement\n\n"
            f"Contexte JSON compact:\n{json.dumps(context, ensure_ascii=False, separators=(',', ':'))}"
        )

    def _extract_level(self, summary: str, context: dict[str, Any]) -> str:
        upper = summary.upper()
        for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if level in upper:
                return level
        global_score = int(context.get("global_score", 0))
        if global_score >= 75:
            return "CRITICAL"
        if global_score >= 50:
            return "HIGH"
        if global_score >= 25:
            return "MEDIUM"
        return "LOW"

    def _extract_bullets(self, summary: str, prefix: str) -> list[str]:
        lines = [line.strip("- ").strip() for line in summary.splitlines() if line.strip()]
        return [line for line in lines if ":" in line or line.lower().startswith(prefix.lower())][:5]

    def _extract_model_names(self, payload: dict[str, Any]) -> list[str]:
        models = payload.get("models", [])
        names: list[str] = []
        for model in models:
            name = str(model.get("name", "")).strip()
            if name:
                names.append(name)
        return names

    def _build_error_detail(self, exc: Exception) -> str:
        response = getattr(exc, "response", None)
        if response is not None:
            try:
                payload = response.json()
                error_text = payload.get("error")
                if error_text:
                    if "not found" in str(error_text).lower() and self.model in str(error_text):
                        return (
                            f"Analyse IA indisponible: le modele Ollama '{self.model}' est introuvable sur ce poste."
                        )
                    return f"Analyse IA indisponible: {error_text}"
            except ValueError:
                pass
        return f"Analyse IA indisponible: {exc}"

    def _build_error_recommendations(self, exc: Exception) -> list[str]:
        response = getattr(exc, "response", None)
        if response is not None:
            try:
                payload = response.json()
                error_text = str(payload.get("error", ""))
                if "not found" in error_text.lower() and self.model in error_text:
                    return [
                        "Installer le modele configure dans Ollama ou selectionner un modele deja present dans les parametres.",
                        "Verifier la liste des modeles avec 'ollama list'.",
                    ]
            except ValueError:
                pass
        return ["Verifier que le service Ollama local est demarre et que le modele est present."]
