from __future__ import annotations

import logging
from typing import Any, Callable

from tkinter import ttk

from app.utils.windows import freeze_redraw, redraw_widget


LOGGER = logging.getLogger(__name__)


class BaseView(ttk.Frame):
    view_title = ""

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, padding=18)
        self.controller = controller
        self.app = app
        self._scheduled_refresh_id: str | None = None
        self._refresh_impl = self.refresh_data
        self._resize_impl = self.on_host_resize
        if getattr(self._refresh_impl, "__func__", None) is not BaseView.refresh_data:
            self.refresh_data = self._safe_refresh_data  # type: ignore[method-assign]
        if getattr(self._resize_impl, "__func__", None) is not BaseView.on_host_resize:
            self.on_host_resize = self._safe_on_host_resize  # type: ignore[method-assign]

    def refresh_data(self) -> None:
        """Override in subclasses."""

    def on_host_resize(self, width: int, height: int) -> None:
        """Override in subclasses when the layout needs responsive adjustments."""

    def reset_scroll_position(self) -> None:
        """Override in scrollable views when switching back to the page should reset its viewport."""

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
        try:
            self.update_idletasks()
        except Exception:
            pass

    def _safe_refresh_data(self) -> None:
        with freeze_redraw(self.app):
            self._refresh_impl()
            force_layout = getattr(getattr(self, "page", None), "force_layout", None)
            if callable(force_layout):
                force_layout()
            try:
                self.update_idletasks()
            except Exception:
                pass
        redraw_widget(self.app)

    def _safe_on_host_resize(self, width: int, height: int) -> None:
        with freeze_redraw(self.app):
            self._resize_impl(width, height)
            force_layout = getattr(getattr(self, "page", None), "force_layout", None)
            if callable(force_layout):
                force_layout()
            try:
                self.update_idletasks()
            except Exception:
                pass
        redraw_widget(self.app)

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
