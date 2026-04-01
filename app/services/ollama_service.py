from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any

from app.models.entities import AIAnalysis, HealthStatus
from app.utils.datetime import utc_now
from app.utils.validation import is_local_http_url

try:
    import requests
except ImportError:  # pragma: no cover - optional during tests
    requests = None


LOGGER = logging.getLogger(__name__)
ALLOWED_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
MAX_SUMMARY_LENGTH = 120
MAX_LIST_ITEMS = 2


class OllamaService:
    def __init__(self, base_url: str, model: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def update(self, *, base_url: str, model: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def health_check(self, demo_mode: bool = False) -> HealthStatus:
        if demo_mode:
            return HealthStatus(
                "ollama",
                "ok",
                "Mode demo: Ollama non interroge, analyse simulee.",
                utc_now(),
            )
        if not is_local_http_url(self.base_url):
            return HealthStatus(
                "ollama",
                "warning",
                "Configuration Ollama refusee: l'URL doit rester locale (localhost, 127.0.0.1 ou ::1).",
                utc_now(),
            )
        if requests is None:
            return HealthStatus("ollama", "error", "La dependance requests est indisponible.", utc_now())
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=min(self.timeout_seconds, 3))
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Reponse JSON Ollama inattendue.")
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
        except self._request_exception_cls() as exc:
            return HealthStatus("ollama", "warning", f"Ollama indisponible: {exc}", utc_now())
        except ValueError as exc:
            return HealthStatus("ollama", "warning", f"Reponse Ollama invalide: {exc}", utc_now())

    def analyze(self, context: dict[str, Any], demo_mode: bool = False) -> AIAnalysis:
        if demo_mode:
            return self._build_demo_analysis(context)
        if not is_local_http_url(self.base_url):
            return self._build_error_analysis(
                context=context,
                summary="Analyse IA refusee: l'URL Ollama doit rester locale (localhost, 127.0.0.1 ou ::1).",
                recommendations=["Remettre une URL locale Ollama dans les parametres avant de relancer l'analyse."],
            )
        if requests is None:
            return self._build_error_analysis(
                context=context,
                summary="Analyse IA impossible: dependance requests absente.",
                recommendations=["Installer les dependances runtime avant d'utiliser l'analyse IA."],
            )

        payload = {
            "model": self.model,
            "prompt": self._build_prompt(context),
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 180,
            },
        }
        data = self._call_ollama(payload)
        raw_response = json.dumps(data, ensure_ascii=False)
        error_detail = str(data.get("_wirewall_error_detail", "")).strip()
        if error_detail:
            return self._build_error_analysis(
                context=context,
                summary=error_detail,
                recommendations=self._normalize_items(data.get("_wirewall_error_recommendations")),
                raw_response=raw_response,
            )

        raw_text = str(data.get("response", "")).strip()
        if not raw_text:
            return self._build_error_analysis(
                context=context,
                summary="Analyse IA indisponible: Ollama n'a pas retourne de contenu exploitable.",
                recommendations=["Verifier le modele local et reessayer l'analyse."],
                raw_response=raw_response,
            )

        parsed = self._parse_response(raw_text)
        normalized, success = self._normalize_response(parsed)
        return AIAnalysis(
            created_at=utc_now(),
            model=self.model,
            global_level=normalized["niveau"],
            summary=normalized["resume"],
            threats=normalized["menaces"],
            recommendations=normalized["actions"],
            raw_response=raw_response,
            success=success,
            context=context,
        )

    def _build_prompt(self, context: dict[str, Any]) -> str:
        return (
            "Tu es un analyste cybersecurite local pour une application Windows de surveillance USB.\n"
            "Reponds uniquement avec un objet JSON valide.\n"
            "N'ajoute aucun markdown, aucune phrase d'introduction, aucun commentaire et aucun texte avant ou apres le JSON.\n"
            "Utilise exactement cette structure:\n"
            '{"niveau":"LOW | MEDIUM | HIGH | CRITICAL","resume":"Phrase courte decrivant la situation (max 120 chars)","menaces":["menace 1","menace 2"],"actions":["action recommandee 1","action recommandee 2"]}\n'
            "Contraintes:\n"
            "- resume en francais, maximum 120 caracteres\n"
            "- menaces: 2 elements maximum\n"
            "- actions: 2 elements maximum\n"
            "- niveau doit etre LOW, MEDIUM, HIGH ou CRITICAL\n\n"
            f"Contexte JSON compact:\n{json.dumps(context, ensure_ascii=False, separators=(',', ':'))}"
        )

    def _call_ollama(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _request() -> Any:
            response = requests.post(  # type: ignore[union-attr]
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(_request)
        try:
            result = future.result(timeout=self.timeout_seconds)
            if isinstance(result, dict):
                return result
            LOGGER.warning("Reponse Ollama JSON inattendue: %s", type(result).__name__)
            return {
                "response": "",
                "_wirewall_error_detail": "Analyse IA indisponible: reponse Ollama invalide.",
                "_wirewall_error_recommendations": ["Verifier que le service Ollama local renvoie un JSON valide."],
            }
        except FuturesTimeout:
            LOGGER.warning("Ollama timeout apres %ss", self.timeout_seconds)
            future.cancel()
            return {
                "response": "",
                "_wirewall_error_detail": f"Analyse IA indisponible: timeout Ollama apres {self.timeout_seconds}s.",
                "_wirewall_error_recommendations": [
                    "Verifier que le service Ollama local est demarre.",
                    "Augmenter le timeout Ollama ou utiliser un modele local plus leger.",
                ],
            }
        except Exception as exc:  # pragma: no cover - asynchronous safety net
            LOGGER.exception("Erreur appel Ollama : %s", exc)
            return {
                "response": "",
                "_wirewall_error_detail": self._build_error_detail(exc),
                "_wirewall_error_recommendations": self._build_error_recommendations(exc),
            }
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _parse_response(self, raw: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return self._fallback_response()

    def _normalize_response(self, payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        fallback = self._fallback_response()
        if payload == fallback:
            return fallback, False

        level = str(payload.get("niveau", "")).strip().upper()
        summary = self._truncate_text(str(payload.get("resume", "")).strip())
        threats = self._normalize_items(payload.get("menaces"))
        actions = self._normalize_items(payload.get("actions"))

        normalized = {
            "niveau": level if level in ALLOWED_LEVELS else "UNKNOWN",
            "resume": summary or fallback["resume"],
            "menaces": threats,
            "actions": actions,
        }
        success = normalized["niveau"] in ALLOWED_LEVELS and bool(summary)
        if not success:
            normalized["niveau"] = "UNKNOWN"
            if not summary:
                normalized["resume"] = fallback["resume"]
        return normalized, success

    def _build_demo_analysis(self, context: dict[str, Any]) -> AIAnalysis:
        score = self._parse_int(context.get("global_score"), default=0)
        level = self._level_from_score(score)
        summary_block = context.get("summary")
        summary_data = summary_block if isinstance(summary_block, dict) else {}
        alert_total = self._parse_int(summary_data.get("alert_total"), default=len(self._context_list(context.get("alerts"))))
        device_total = self._parse_int(summary_data.get("device_total"), default=len(self._context_list(context.get("devices"))))

        if alert_total > 0:
            summary = self._truncate_text(
                f"Mode demo: risque {level} sur {alert_total} alerte(s) et {device_total} peripherique(s)."
            )
            actions = [
                "Verifier les alertes actives et l'historique recent avant validation utilisateur.",
                "Confirmer l'identite des peripheriques relies avant toute decision.",
            ]
        else:
            summary = self._truncate_text("Mode demo: environnement stable, aucune alerte critique detectee.")
            actions = [
                "Poursuivre la surveillance locale des peripheriques USB.",
                "Relancer une analyse apres un nouvel evenement ou une alerte.",
            ]

        threats = self._build_demo_threats(context.get("alerts"))
        payload = {
            "niveau": level,
            "resume": summary,
            "menaces": threats,
            "actions": actions[:MAX_LIST_ITEMS],
        }
        return AIAnalysis(
            created_at=utc_now(),
            model=self.model,
            global_level=payload["niveau"],
            summary=payload["resume"],
            threats=payload["menaces"],
            recommendations=payload["actions"],
            raw_response=json.dumps(payload, ensure_ascii=False),
            success=True,
            context=context,
        )

    def _build_demo_threats(self, alerts_value: Any) -> list[str]:
        threats: list[str] = []
        for alert in self._context_list(alerts_value)[:MAX_LIST_ITEMS]:
            if not isinstance(alert, dict):
                continue
            title = str(alert.get("title", "")).strip()
            message = str(alert.get("message", "")).strip()
            severity = str(alert.get("severity", "")).strip().upper()
            detail = title or message
            if not detail:
                continue
            prefix = f"{severity}: " if severity else ""
            threats.append(self._truncate_text(f"{prefix}{detail}"))
        return threats[:MAX_LIST_ITEMS]

    def _extract_model_names(self, payload: dict[str, Any]) -> list[str]:
        models = payload.get("models", [])
        names: list[str] = []
        for model in models:
            name = str(model.get("name", "")).strip()
            if name:
                names.append(name)
        return names

    def _build_error_analysis(
        self,
        *,
        context: dict[str, Any],
        summary: str,
        recommendations: list[str],
        raw_response: str = "",
    ) -> AIAnalysis:
        return AIAnalysis(
            created_at=utc_now(),
            model=self.model,
            global_level="UNKNOWN",
            summary=self._truncate_text(summary) or self._fallback_response()["resume"],
            recommendations=recommendations[:MAX_LIST_ITEMS],
            raw_response=raw_response,
            success=False,
            context=context,
        )

    def _build_error_detail(self, exc: Exception) -> str:
        response = getattr(exc, "response", None)
        if response is not None:
            try:
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("Reponse JSON Ollama inattendue.")
                error_text = payload.get("error")
                if error_text:
                    if "not found" in str(error_text).lower() and self.model in str(error_text):
                        return f"Analyse IA indisponible: le modele Ollama '{self.model}' est introuvable sur ce poste."
                    return f"Analyse IA indisponible: {error_text}"
            except ValueError:
                pass
        return f"Analyse IA indisponible: {exc}"

    def _build_error_recommendations(self, exc: Exception) -> list[str]:
        response = getattr(exc, "response", None)
        if response is not None:
            try:
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("Reponse JSON Ollama inattendue.")
                error_text = str(payload.get("error", ""))
                if "not found" in error_text.lower() and self.model in error_text:
                    return [
                        "Installer le modele configure dans Ollama ou selectionner un modele deja present dans les parametres.",
                        "Verifier la liste des modeles avec 'ollama list'.",
                    ]
            except ValueError:
                pass
        return ["Verifier que le service Ollama local est demarre et que le modele est present."]

    def _fallback_response(self) -> dict[str, Any]:
        return {
            "niveau": "UNKNOWN",
            "resume": "Analyse non disponible (reponse invalide du modele).",
            "menaces": [],
            "actions": [],
        }

    def _normalize_items(self, value: Any) -> list[str]:
        if isinstance(value, str):
            candidates = [value]
        elif isinstance(value, (list, tuple)):
            candidates = list(value)
        else:
            candidates = []
        normalized: list[str] = []
        for item in candidates:
            text = self._truncate_text(str(item).strip())
            if text:
                normalized.append(text)
            if len(normalized) >= MAX_LIST_ITEMS:
                break
        return normalized

    def _level_from_score(self, score: int) -> str:
        if score >= 75:
            return "CRITICAL"
        if score >= 50:
            return "HIGH"
        if score >= 25:
            return "MEDIUM"
        return "LOW"

    def _parse_int(self, value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _truncate_text(self, value: str, max_length: int = MAX_SUMMARY_LENGTH) -> str:
        text = value.strip()
        if len(text) <= max_length:
            return text
        return text[:max_length].rstrip()

    def _context_list(self, value: Any) -> list[Any]:
        return list(value) if isinstance(value, list) else []

    def _request_exception_cls(self):
        if requests is None:
            return Exception
        return getattr(requests, "RequestException", Exception)
