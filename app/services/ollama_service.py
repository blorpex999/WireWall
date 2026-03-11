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
            return HealthStatus("ollama", "error", "La dépendance requests est indisponible.", utc_now())
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=min(self.timeout_seconds, 3))
            if response.ok:
                return HealthStatus("ollama", "ok", "Ollama répond localement.", utc_now())
            return HealthStatus("ollama", "warning", f"Ollama a répondu {response.status_code}.", utc_now())
        except requests.RequestException as exc:
            return HealthStatus("ollama", "warning", f"Ollama indisponible: {exc}", utc_now())

    def analyze(self, context: dict[str, Any]) -> AIAnalysis:
        if requests is None:
            return AIAnalysis(
                created_at=utc_now(),
                model=self.model,
                global_level="UNKNOWN",
                summary="Analyse IA impossible: dépendance requests absente.",
                recommendations=["Installer les dépendances runtime avant d'utiliser l'analyse IA."],
                raw_response="",
                success=False,
                context=context,
            )

        prompt = self._build_prompt(context)
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
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
                    summary="Ollama n'a pas retourné de contenu exploitable.",
                    recommendations=["Vérifier le modèle local et réessayer l'analyse."],
                    raw_response=json.dumps(data, ensure_ascii=False),
                    success=False,
                    context=context,
                )
            summary = raw_text
            level = self._extract_level(summary, context)
            threats = self._extract_bullets(summary, prefix="Menace")
            recommendations = self._extract_bullets(summary, prefix="Action")
            if not recommendations:
                recommendations = ["Vérifier les périphériques actifs et les alertes avant validation utilisateur."]
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
        except (requests.RequestException, ValueError) as exc:
            return AIAnalysis(
                created_at=utc_now(),
                model=self.model,
                global_level="UNKNOWN",
                summary=f"Analyse IA indisponible: {exc}",
                recommendations=["Vérifier que le service Ollama local est démarré et que le modèle est présent."],
                raw_response="",
                success=False,
                context=context,
            )

    def _build_prompt(self, context: dict[str, Any]) -> str:
        return (
            "Tu es un analyste cybersécurité local.\n"
            "Analyse le contexte USB Windows ci-dessous et réponds en français.\n"
            "Donne: 1) résumé, 2) menaces probables, 3) niveau global LOW/MEDIUM/HIGH/CRITICAL, 4) recommandations.\n\n"
            f"Contexte JSON:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
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
