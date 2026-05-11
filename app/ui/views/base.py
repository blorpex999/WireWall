from __future__ import annotations

import logging
from typing import Any, Callable

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget

from app.ui.widgets.common import ScrollablePage

LOGGER = logging.getLogger(__name__)


class BaseView(QWidget):
    view_title = ""

    def __init__(self, parent: QWidget, controller, app) -> None:
        super().__init__(parent)
        self.controller = controller
        self.app = app
        self._scheduled_refresh_timer: QTimer | None = None

    def refresh_data(self) -> None:
        """Override in subclasses."""

    def on_host_resize(self, width: int, height: int) -> None:
        """Override in subclasses when the layout needs responsive adjustments."""

    def reset_scroll_position(self) -> None:
        """Override in scrollable views when switching back to the page should reset its viewport."""

    def schedule_refresh(self, delay_ms: int = 250) -> None:
        self.cancel_scheduled_refresh()
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(self._run_scheduled_refresh)
        timer.start(delay_ms)
        self._scheduled_refresh_timer = timer

    def cancel_scheduled_refresh(self) -> None:
        if self._scheduled_refresh_timer is None:
            return
        self._scheduled_refresh_timer.stop()
        self._scheduled_refresh_timer.deleteLater()
        self._scheduled_refresh_timer = None

    def _run_scheduled_refresh(self) -> None:
        self._scheduled_refresh_timer = None
        try:
            self.refresh_preserving_scroll()
        except Exception:
            LOGGER.exception("Erreur dans refresh_data() de %s.", self.__class__.__name__)

    def refresh_preserving_scroll(self) -> None:
        pages = self.findChildren(ScrollablePage)
        states = [(page, page.capture_scroll_state()) for page in pages]
        self.refresh_data()
        for page, state in states:
            page.restore_scroll_state(state)

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
            self.refresh_preserving_scroll()
        if success_message:
            message = success_message(result) if callable(success_message) else success_message
            level = success_level(result) if callable(success_level) else success_level
            self.app.set_status(message, level)
        return result

    def set_status(self, message: str, level: str = "INFO") -> None:
        self.app.set_status(message, level)
