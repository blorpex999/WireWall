from __future__ import annotations

import logging
from typing import Any, Callable

from tkinter import ttk


LOGGER = logging.getLogger(__name__)


class BaseView(ttk.Frame):
    view_title = ""

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, padding=18)
        self.controller = controller
        self.app = app
        self._scheduled_refresh_id: str | None = None

    def refresh_data(self) -> None:
        """Override in subclasses."""

    def on_host_resize(self, width: int, height: int) -> None:
        """Override in subclasses when the layout needs responsive adjustments."""

    def schedule_refresh(self, delay_ms: int = 250) -> None:
        self.cancel_scheduled_refresh()
        self._scheduled_refresh_id = self.after(delay_ms, self._run_scheduled_refresh)

    def cancel_scheduled_refresh(self) -> None:
        if self._scheduled_refresh_id is None:
            return
        try:
            self.after_cancel(self._scheduled_refresh_id)
        except Exception:
            pass
        self._scheduled_refresh_id = None

    def _run_scheduled_refresh(self) -> None:
        self._scheduled_refresh_id = None
        self.refresh_data()

    def run_action(
        self,
        action: Callable[[], Any],
        *,
        success_message: str | Callable[[Any], str] | None = None,
        success_level: str | Callable[[Any], str] = "OK",
        refresh: bool = False,
    ) -> Any | None:
        try:
            result = action()
        except ValueError as exc:
            self.app.set_status(str(exc), "WARNING")
            return None
        except RuntimeError as exc:
            LOGGER.exception("Erreur applicative dans la vue %s", self.view_title)
            self.app.set_status(str(exc), "ERROR")
            return None
        except OSError as exc:
            LOGGER.exception("Erreur systeme dans la vue %s", self.view_title)
            self.app.set_status(f"Erreur systeme: {exc}", "ERROR")
            return None
        except Exception as exc:  # pragma: no cover - UI safety net
            LOGGER.exception("Erreur inattendue dans la vue %s", self.view_title)
            self.app.set_status(f"Erreur inattendue: {exc}", "ERROR")
            return None

        if refresh:
            self.refresh_data()
        if success_message:
            message = success_message(result) if callable(success_message) else success_message
            level = success_level(result) if callable(success_level) else success_level
            self.app.set_status(message, level)
        return result
