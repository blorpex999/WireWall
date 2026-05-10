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
MAX_SUMMARY_LENGTH = 420
MAX_LIST_ITEMS = 5
MAX_RAW_RESPONSE_LENGTH = 8000
FAST_MODEL_CANDIDATES = ("qwen2.5:3b", "qwen2.5:7b", "mistral:latest")


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

        analysis_model = self._select_analysis_model()
        payload = {
            "model": analysis_model,
            "prompt": self._build_prompt(context),
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": 700,
            },
        }
        data = self._call_ollama(payload)
        raw_response = self._safe_raw_response(data)
        error_detail = str(data.get("_wirewall_error_detail", "")).strip()
        if error_detail:
            if self._can_use_contextual_fallback(error_detail):
                fallback = self._build_contextual_analysis(context=context, raw_response=raw_response, model=analysis_model)
                fallback.recommendations = (
                    fallback.recommendations + self._normalize_items(data.get("_wirewall_error_recommendations"))
                )[:MAX_LIST_ITEMS]
                return fallback
            return self._build_error_analysis(
                context=context,
                summary=error_detail,
                recommendations=self._normalize_items(data.get("_wirewall_error_recommendations")),
                raw_response=raw_response,
                model=analysis_model,
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
        if not success:
            return self._build_contextual_analysis(context=context, raw_response=raw_response, model=analysis_model)
        normalized["niveau"] = self._raise_level_from_context(str(normalized["niveau"]), context)
        return AIAnalysis(
            created_at=utc_now(),
            model=analysis_model,
            global_level=normalized["niveau"],
            summary=normalized["resume"],
            threats=normalized["menaces"],
            recommendations=normalized["actions"],
            raw_response=raw_response,
            success=success,
            context=context,
        )

    def _build_prompt(self, context: dict[str, Any]) -> str:
        context_json = json.dumps(self._prompt_context(context), ensure_ascii=False, separators=(",", ":"))
        return (
            "Tu es un analyste cybersecurite local pour une application Windows de surveillance USB.\n"
            "Ta reponse doit etre directement exploitable par un analyste humain.\n"
            "Reponds uniquement avec un objet JSON valide, sans markdown et sans texte autour.\n"
            "Utilise exactement ces cles:\n"
            '{"niveau":"LOW|MEDIUM|HIGH|CRITICAL","resume":"Analyse en 3 a 5 phrases concretes.","menaces":["anomalie detaillee 1"],"actions":["action analyste 1"]}\n'
            "Contraintes:\n"
            "- resume en francais, 3 a 5 phrases, cite les chiffres utiles du contexte\n"
            "- menaces: 3 a 5 elements maximum, precis, relies aux devices/alertes/incidents\n"
            "- actions: 3 a 5 elements maximum, faisables par un analyste, sans action destructive\n"
            "- niveau doit etre LOW, MEDIUM, HIGH ou CRITICAL\n\n"
            "Priorites d'analyse:\n"
            "1. Alertes non acquittees et incidents ouverts.\n"
            "2. Peripheriques NEW, RARE ou DEVIATION.\n"
            "3. Scores HIGH/CRITICAL, evenements recents, decisions analyste manquantes.\n"
            "4. Si un marqueur de simulation USB est present, decris-le comme scenario controle, pas comme infection reelle.\n\n"
            f"Contexte JSON compact:\n{context_json}"
        )

    def _call_ollama(self, payload: dict[str, Any]) -> dict[str, Any]:
        timeout_seconds = self._request_timeout_for_model(str(payload.get("model") or self.model))

        def _request() -> Any:
            response = requests.post(  # type: ignore[union-attr]
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout_seconds,
            )
            response.raise_for_status()
            return response.json()

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(_request)
        try:
            result = future.result(timeout=timeout_seconds)
            if isinstance(result, dict):
                return result
            LOGGER.warning("Reponse Ollama JSON inattendue: %s", type(result).__name__)
            return {
                "response": "",
                "_wirewall_error_detail": "Analyse IA indisponible: reponse Ollama invalide.",
                "_wirewall_error_recommendations": ["Verifier que le service Ollama local renvoie un JSON valide."],
            }
        except FuturesTimeout:
            LOGGER.warning("Ollama timeout apres %ss", timeout_seconds)
            future.cancel()
            return {
                "response": "",
                "_wirewall_error_detail": f"Analyse IA indisponible: timeout Ollama apres {timeout_seconds}s.",
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

        level = str(payload.get("niveau") or payload.get("level") or "").strip().upper()
        summary = self._truncate_text(str(payload.get("resume") or payload.get("summary") or "").strip())
        threats = self._normalize_items(payload.get("menaces") or payload.get("threats") or payload.get("anomalies"))
        actions = self._normalize_items(payload.get("actions") or payload.get("recommendations"))

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

    def _build_contextual_analysis(self, *, context: dict[str, Any], raw_response: str = "", model: str | None = None) -> AIAnalysis:
        summary_data = context.get("summary") if isinstance(context.get("summary"), dict) else {}
        alerts = [item for item in self._context_list(context.get("alerts")) if isinstance(item, dict)]
        devices = [item for item in self._context_list(context.get("devices")) if isinstance(item, dict)]
        incidents = [item for item in self._context_list(context.get("incidents")) if isinstance(item, dict)]
        suggestions = [item for item in self._context_list(context.get("suggestions")) if isinstance(item, dict)]
        brain_memory = context.get("brain_memory") if isinstance(context.get("brain_memory"), dict) else {}

        level = self._context_level(context, alerts, devices, brain_memory)
        alert_total = self._parse_int(summary_data.get("alert_total"), default=len(alerts))
        incident_total = self._parse_int(summary_data.get("incident_total"), default=len(incidents))
        device_total = self._parse_int(summary_data.get("device_total"), default=len(devices))
        connected_total = self._parse_int(summary_data.get("connected_total"), default=0)
        deviation_total = self._parse_int(summary_data.get("deviation_total"), default=0)
        new_device_total = self._parse_int(summary_data.get("new_device_total"), default=0)

        top_alert = alerts[0] if alerts else {}
        top_alert_title = str(top_alert.get("title") or "").strip()
        top_alert_severity = str(top_alert.get("severity") or "").strip().upper()
        focus = top_alert_title or self._first_device_name(devices) or "surveillance USB courante"
        summary = (
            f"Analyse locale de secours: niveau {level} sur {device_total} peripherique(s), "
            f"dont {connected_total} connecte(s). {alert_total} alerte(s) et {incident_total} incident(s) sont a suivre. "
            f"Le point prioritaire est {focus}"
            f"{f' ({top_alert_severity})' if top_alert_severity else ''}. "
            f"Le contexte signale {new_device_total} nouveau(x) peripherique(s) et {deviation_total} deviation(s)."
        )

        threats = self._derive_threats(alerts, devices)
        actions = self._derive_actions(alerts, devices, incidents, suggestions)
        payload = {
            "niveau": level,
            "resume": self._truncate_text(summary),
            "menaces": threats,
            "actions": actions,
            "source": "local_contextual_fallback",
        }
        return AIAnalysis(
            created_at=utc_now(),
            model=model or self.model,
            global_level=payload["niveau"],
            summary=payload["resume"],
            threats=payload["menaces"],
            recommendations=payload["actions"],
            raw_response=raw_response or json.dumps(payload, ensure_ascii=False),
            success=True,
            context=context,
        )

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

    def _context_level(
        self,
        context: dict[str, Any],
        alerts: list[dict[str, Any]],
        devices: list[dict[str, Any]],
        brain_memory: dict[str, Any],
    ) -> str:
        levels = [str(brain_memory.get("global_level") or "").strip().upper()]
        levels.append(self._level_from_score(self._parse_int(context.get("global_score"), default=0)))
        for alert in alerts:
            levels.append(str(alert.get("severity") or "").strip().upper())
        for device in devices:
            levels.append(str(device.get("risk_level") or "").strip().upper())
        return max((level for level in levels if level in ALLOWED_LEVELS), key=self._level_rank, default="LOW")

    def _raise_level_from_context(self, model_level: str, context: dict[str, Any]) -> str:
        alerts = [item for item in self._context_list(context.get("alerts")) if isinstance(item, dict)]
        devices = [item for item in self._context_list(context.get("devices")) if isinstance(item, dict)]
        brain_memory = context.get("brain_memory") if isinstance(context.get("brain_memory"), dict) else {}
        context_level = self._context_level(context, alerts, devices, brain_memory)
        if self._level_rank(context_level) > self._level_rank(model_level):
            return context_level
        return model_level if model_level in ALLOWED_LEVELS else context_level

    def _derive_threats(self, alerts: list[dict[str, Any]], devices: list[dict[str, Any]]) -> list[str]:
        threats: list[str] = []
        for alert in alerts:
            title = str(alert.get("title") or "").strip()
            message = str(alert.get("message") or "").strip()
            severity = str(alert.get("severity") or "").strip().upper()
            score = self._parse_int(alert.get("score"), default=0)
            if not title and not message:
                continue
            prefix = f"Alerte {severity}" if severity else "Alerte"
            detail = title or message
            extra = f" score {score}" if score else ""
            threats.append(self._truncate_text(f"{prefix}: {detail}.{extra}", 220))
            if len(threats) >= MAX_LIST_ITEMS:
                return threats
        for device in devices:
            trust_state = str(device.get("trust_state") or "").strip().upper()
            risk_level = str(device.get("risk_level") or "").strip().upper()
            risk_score = self._parse_int(device.get("risk_score"), default=0)
            if trust_state not in {"NEW", "RARE", "DEVIATION"} and risk_level not in {"HIGH", "CRITICAL"}:
                continue
            name = str(device.get("name") or device.get("device_key") or "Peripherique USB").strip()
            threats.append(
                self._truncate_text(
                    f"{name}: etat {trust_state or 'inconnu'}, risque {risk_level or 'UNKNOWN'} ({risk_score}).",
                    220,
                )
            )
            if len(threats) >= MAX_LIST_ITEMS:
                return threats
        return threats or ["Aucune anomalie forte isolee; continuer la surveillance et confirmer la baseline."]

    def _derive_actions(
        self,
        alerts: list[dict[str, Any]],
        devices: list[dict[str, Any]],
        incidents: list[dict[str, Any]],
        suggestions: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if alerts:
            actions.append("Traiter d'abord les alertes non acquittees et documenter la decision analyste dans l'incident.")
        hot_device = self._first_device_name(devices)
        if hot_device:
            actions.append(f"Verifier l'identite et l'usage attendu de {hot_device} avant whitelist ou blacklist.")
        if incidents:
            actions.append("Mettre a jour les incidents ouverts avec statut, commentaire, decision et raison de resolution.")
        if suggestions:
            actions.append("Valider ou rejeter les suggestions supervisees pour stabiliser la baseline WireWall.")
        if any("simulation" in str(alert.get("title") or "").lower() for alert in alerts):
            actions.append("Presenter le support USB comme scenario controle et retirer le disque apres la demonstration.")
        actions.append("Relancer une analyse apres debranchement/rebranchement ou apres correction des alertes.")
        return actions[:MAX_LIST_ITEMS]

    def _first_device_name(self, devices: list[dict[str, Any]]) -> str:
        for device in devices:
            name = str(device.get("name") or "").strip()
            if name:
                return name
        return ""

    def _level_rank(self, level: str) -> int:
        return {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(level.upper(), 0)

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
        model: str | None = None,
    ) -> AIAnalysis:
        return AIAnalysis(
            created_at=utc_now(),
            model=model or self.model,
            global_level="UNKNOWN",
            summary=self._truncate_text(summary) or self._fallback_response()["resume"],
            recommendations=recommendations[:MAX_LIST_ITEMS],
            raw_response=raw_response,
            success=False,
            context=context,
        )

    def _select_analysis_model(self) -> str:
        if not self._is_heavy_model(self.model):
            return self.model
        names = self._available_model_names()
        for candidate in FAST_MODEL_CANDIDATES:
            if candidate in names:
                return candidate
        return self.model

    def _available_model_names(self) -> list[str]:
        if requests is None or not is_local_http_url(self.base_url):
            return []
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                return []
            return self._extract_model_names(payload)
        except self._request_exception_cls():
            return []
        except ValueError:
            return []

    def _is_heavy_model(self, model: str) -> bool:
        normalized = model.lower()
        return any(token in normalized for token in (":13b", ":14b", ":30b", ":32b", ":70b"))

    def _request_timeout_for_model(self, model: str) -> int | float:
        cap = 120 if self._is_heavy_model(model) else 45
        return min(self.timeout_seconds, cap)

    def _can_use_contextual_fallback(self, detail: str) -> bool:
        normalized = detail.lower()
        return "timeout ollama" in normalized or "reponse ollama invalide" in normalized

    def _prompt_context(self, context: dict[str, Any]) -> dict[str, Any]:
        brain_memory = context.get("brain_memory") if isinstance(context.get("brain_memory"), dict) else None
        compact_brain = None
        if brain_memory is not None:
            compact_brain = {
                "global_level": brain_memory.get("global_level"),
                "progress_status": brain_memory.get("progress_status"),
                "global_score": brain_memory.get("global_score"),
                "incident_count": brain_memory.get("incident_count"),
                "open_alert_count": brain_memory.get("open_alert_count"),
                "summary": brain_memory.get("summary"),
                "recommendations": self._context_list(brain_memory.get("recommendations"))[:3],
                "focus_areas": self._context_list(brain_memory.get("focus_areas"))[:3],
            }
        return {
            "generated_at": context.get("generated_at"),
            "mode": context.get("mode"),
            "global_score": context.get("global_score"),
            "summary": context.get("summary"),
            "devices": self._context_list(context.get("devices"))[:4],
            "alerts": self._context_list(context.get("alerts"))[:4],
            "recent_events": self._context_list(context.get("recent_events"))[:6],
            "incidents": self._context_list(context.get("incidents"))[:3],
            "suggestions": self._context_list(context.get("suggestions"))[:3],
            "recent_ai_observations": self._context_list(context.get("recent_ai_observations"))[:1],
            "brain_memory": compact_brain,
        }

    def _safe_raw_response(self, data: dict[str, Any]) -> str:
        keep_keys = (
            "model",
            "created_at",
            "response",
            "done",
            "done_reason",
            "total_duration",
            "load_duration",
            "prompt_eval_count",
            "eval_count",
            "error",
            "_wirewall_error_detail",
            "_wirewall_error_recommendations",
        )
        safe: dict[str, Any] = {key: data[key] for key in keep_keys if key in data}
        if "response" in safe:
            safe["response"] = self._truncate_text(str(safe["response"]), 5000)
        return self._truncate_text(json.dumps(safe or data, ensure_ascii=False), MAX_RAW_RESPONSE_LENGTH)

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
