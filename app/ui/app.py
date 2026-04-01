from __future__ import annotations

import logging
import platform

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QCloseEvent, QIcon, QPixmap, QResizeEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from app.ui.controller import AppController
from app.ui.theme import COLORS, get_stylesheet
from app.ui.views.about import AboutView
from app.ui.views.ai_analysis import AIAnalysisView
from app.ui.views.alerts import AlertsView
from app.ui.views.base import BaseView
from app.ui.views.dashboard import DashboardView
from app.ui.views.devices import DevicesView
from app.ui.views.history import HistoryView
from app.ui.views.policies import PoliciesView
from app.ui.views.settings import SettingsView
from app.ui.views.usb_control import USBControlView
from app.ui.widgets.common import DemoBanner, StatusBar, StatusPill
from app.utils.resources import asset_path
from app.utils.windows import WindowsDeviceNotificationFilter
from app.version import __version__

LOGGER = logging.getLogger(__name__)


class WireWallMainWindow(QMainWindow):
    def __init__(self, container) -> None:
        super().__init__()
        self.container = container
        self.controller = AppController(container)
        self.nav_buttons: dict[str, QPushButton] = {}
        self.views: dict[str, BaseView] = {}
        self.current_view_key: str | None = None
        self._investigation_windows: list[QWidget] = []
        self._usb_filter: WindowsDeviceNotificationFilter | None = None
        self._tray_icon: QSystemTrayIcon | None = None
        self._repaint_scheduled = False
        self._force_repaint_running = False
        self._is_closing = False
        self._window_icon = QIcon()

        self.view_specs = [
            ("dashboard", "Tableau de bord", DashboardView),
            ("devices", "Peripheriques", DevicesView),
            ("alerts", "Alertes", AlertsView),
            ("history", "Historique", HistoryView),
            ("policies", "Regles USB", PoliciesView),
            ("usb_control", "Controle USB", USBControlView),
            ("ai_analysis", "Analyse IA", AIAnalysisView),
            ("settings", "Parametres", SettingsView),
            ("about", "A propos", AboutView),
        ]

        self.setWindowTitle(f"WireWall {__version__}")
        self.resize(1450, 920)
        self.setMinimumSize(1180, 780)
        self.setStyleSheet(get_stylesheet())
        self._configure_window_icon()

        root = QWidget(self)
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(8)

        self.banner = DemoBanner(root, visible=self.controller.demo_mode)
        root_layout.addWidget(self.banner)

        shell = QWidget(root)
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(8)
        root_layout.addWidget(shell, 1)

        self.sidebar = self._build_sidebar(shell)
        shell_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget(shell)
        shell_layout.addWidget(self.stack, 1)

        for key, _label, view_class in self.view_specs:
            view = view_class(self.stack, self.controller, self)
            self.views[key] = view
            self.stack.addWidget(view)

        self.status_bar_widget = StatusBar(self)
        self.status_bar_widget.set_mode(self.controller.demo_mode)
        self.setStatusBar(self.status_bar_widget)

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_backend_events)
        self._poll_timer.start(250)

        self._periodic_timer = QTimer(self)
        self._periodic_timer.setSingleShot(True)
        self._periodic_timer.timeout.connect(self._periodic_refresh)

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._handle_resize_settle)

        self._setup_tray_icon()
        self._install_native_usb_filter()
        self._refresh_mode_badges()
        self._schedule_periodic_refresh()

        self.controller.start_services()
        self.show_view("dashboard")
        self.controller.request_health_refresh()
        self.controller.request_brain_refresh()
        self.set_status("WireWall initialise.", "OK")
        QTimer.singleShot(150, self._notify_view_resize)

    def _build_sidebar(self, parent: QWidget) -> QFrame:
        sidebar = QFrame(parent)
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QWidget(sidebar)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 2, 4, 16)
        header_layout.setSpacing(10)
        layout.addWidget(header)

        logo_label = QLabel(header)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        logo_pixmap = self._load_logo_pixmap()
        if logo_pixmap is not None:
            logo_label.setPixmap(logo_pixmap)
            header_layout.addWidget(logo_label, 0, Qt.AlignmentFlag.AlignTop)

        title_box = QWidget(header)
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        header_layout.addWidget(title_box, 1)

        title = QLabel("WireWall", title_box)
        title.setStyleSheet("font-size: 22pt; font-weight: 600;")
        title_layout.addWidget(title)

        subtitle = QLabel("Surveillance USB Windows", title_box)
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        title_layout.addWidget(subtitle)

        self.sidebar_mode = StatusPill(header, "", "INFO")
        header_layout.addWidget(self.sidebar_mode, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        for key, label, _view_class in self.view_specs:
            button = QPushButton(label, sidebar)
            button.setObjectName("nav_button")
            button.setProperty("active", False)
            button.clicked.connect(lambda _checked=False, value=key: self.show_view(value))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(38)
            layout.addWidget(button)
            self.nav_buttons[key] = button

        layout.addStretch(1)
        return sidebar

    def _load_logo_pixmap(self) -> QPixmap | None:
        for path in (
            asset_path("assets", "wirewall_logo_128.png"),
            asset_path("assets", "wirewall_logo.png"),
        ):
            if not path.exists():
                continue
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                return pixmap.scaled(
                    52,
                    52,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
        return None

    def _configure_window_icon(self) -> None:
        for path in (
            asset_path("assets", "wirewall.ico"),
            asset_path("assets", "wirewall_logo_128.png"),
            asset_path("assets", "wirewall_logo.png"),
        ):
            if not path.exists():
                continue
            icon = QIcon(str(path))
            if icon.isNull():
                continue
            self._window_icon = icon
            self.setWindowIcon(icon)
            app = QApplication.instance()
            if app is not None:
                app.setWindowIcon(icon)
            return

    def _setup_tray_icon(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = self._window_icon
        if icon.isNull():
            return
        tray = QSystemTrayIcon(icon, self)
        tray.setToolTip("WireWall")
        tray.show()
        self._tray_icon = tray

    def _install_native_usb_filter(self) -> None:
        if platform.system() != "Windows":
            return
        app = QApplication.instance()
        if app is None:
            return

        self._usb_filter = WindowsDeviceNotificationFilter(
            lambda _reason, _code: QTimer.singleShot(0, self.controller.refresh_monitor)
        )
        app.installNativeEventFilter(self._usb_filter)

    def show_view(self, name: str) -> None:
        view = self.views[name]
        self.stack.setCurrentWidget(view)
        self.current_view_key = name
        self._refresh_nav_state(name)
        try:
            view.refresh_data()
            view.reset_scroll_position()
        except Exception:
            LOGGER.exception("Erreur lors du chargement de la vue %s.", name)
            self.set_status(f"Erreur de chargement de la vue : {self._view_label(name)}", "ERROR")
        self.setWindowTitle(f"WireWall {__version__} - {self._view_label(name)}")
        self.set_status(f"Vue active : {self._view_label(name)}", "INFO")
        QTimer.singleShot(0, self._notify_view_resize)
        QTimer.singleShot(0, self.request_repaint)

    def show_investigation(self, device_key: str) -> None:
        from app.ui.views.investigation import InvestigationWindow

        window = InvestigationWindow(self, self.controller, device_key)
        self._investigation_windows.append(window)
        window.finished.connect(lambda _code, current=window: self._forget_investigation_window(current))
        window.show()
        window.raise_()
        window.activateWindow()

    def _forget_investigation_window(self, window: QWidget) -> None:
        try:
            self._investigation_windows.remove(window)
        except ValueError:
            pass

    def set_status(self, message: str, level: str = "INFO") -> None:
        self.status_bar_widget.set_status(message, level)

    def _poll_backend_events(self) -> None:
        refresh_views: set[str] = set()
        for event in self.container.event_bus.drain():
            event_type = event["type"]
            if event_type == "device_event":
                self.controller.request_brain_refresh()
                refresh_views.update({"dashboard", "devices", "history", "alerts"})
            elif event_type in {"snapshot_updated", "ai_analysis"}:
                refresh_views.update({"dashboard", "devices", "history", "alerts"})
            elif event_type == "ai_analysis_completed":
                analysis = event["payload"]["result"]
                self.controller.request_brain_refresh()
                self.set_status(
                    "Analyse IA terminee." if analysis.success else analysis.summary,
                    "OK" if analysis.success else "WARNING",
                )
                refresh_views.update({"dashboard", "ai_analysis"})
            elif event_type == "health_refresh_completed":
                self.controller.request_brain_refresh()
                refresh_views.update({"dashboard", "ai_analysis", "usb_control"})
            elif event_type == "brain_refresh_completed":
                refresh_views.add("dashboard")
            elif event_type == "alert_created":
                payload = event["payload"]
                self.controller.request_brain_refresh()
                self.set_status(payload.get("message", "Nouvelle alerte."), payload.get("severity", "WARNING"))
                refresh_views.update({"dashboard", "alerts"})
                if (
                    self.controller.settings.desktop_notifications_enabled
                    and payload.get("severity") in {"HIGH", "CRITICAL"}
                ):
                    self._show_notification_toast(
                        payload.get("title", "Alerte WireWall"),
                        payload.get("message", "Nouvelle alerte."),
                        payload.get("severity", "WARNING"),
                    )
            elif event_type == "monitor_error":
                self.set_status(event["payload"].get("message", "Erreur de monitoring."), "ERROR")
                refresh_views.add("dashboard")
            elif event_type == "monitor_warning":
                self.set_status(event["payload"].get("message", "Degradation du monitoring USB."), "WARNING")
                refresh_views.add("dashboard")
            elif event_type == "background_task_error":
                self.set_status(event["payload"].get("message", "Erreur de tache de fond."), "ERROR")
                task_name = event["payload"].get("task")
                if task_name == "ai_analysis":
                    refresh_views.add("ai_analysis")
                elif task_name == "health_refresh":
                    refresh_views.update({"dashboard", "ai_analysis", "usb_control"})
                elif task_name == "brain_refresh":
                    refresh_views.add("dashboard")

        if refresh_views:
            if "dashboard" in refresh_views:
                self._refresh_view("dashboard")
            if self.current_view_key is not None and self.current_view_key != "dashboard" and self.current_view_key in refresh_views:
                self._refresh_view(self.current_view_key)
            self.request_repaint()

    def _refresh_view(self, key: str) -> None:
        try:
            self.views[key].refresh_data()
        except Exception:
            LOGGER.exception("Erreur pendant le refresh de la vue %s.", key)

    def _schedule_periodic_refresh(self) -> None:
        interval = max(1500, int(self.controller.settings.dashboard_refresh_ms))
        self._periodic_timer.start(interval)

    def _periodic_refresh(self) -> None:
        self.controller.request_health_refresh()
        self._schedule_periodic_refresh()

    def request_repaint(self) -> None:
        if self._repaint_scheduled or self._force_repaint_running:
            return
        self._repaint_scheduled = True
        QTimer.singleShot(0, self._force_repaint)

    def _force_repaint(self) -> None:
        if self._force_repaint_running:
            return
        self._repaint_scheduled = False
        self._force_repaint_running = True
        try:
            self.update()
        except Exception:  # pragma: no cover - UI safety net
            LOGGER.exception("Erreur pendant le repaint force.")
        finally:
            self._force_repaint_running = False

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        if not self._is_closing:
            self._resize_timer.start(100)

    def _handle_resize_settle(self) -> None:
        self._notify_view_resize()
        self.request_repaint()

    def _notify_view_resize(self) -> None:
        if self.current_view_key is None:
            return
        view = self.views.get(self.current_view_key)
        if view is None:
            return
        try:
            view.on_host_resize(self.stack.width(), self.stack.height())
        except Exception:  # pragma: no cover - UI safety net
            LOGGER.exception("Erreur pendant le resize de la vue %s.", self.current_view_key)

    def _refresh_nav_state(self, active_key: str | None = None) -> None:
        target = active_key or self.current_view_key
        for key, button in self.nav_buttons.items():
            button.setProperty("active", key == target)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def _refresh_mode_badges(self) -> None:
        if self.controller.demo_mode:
            self.sidebar_mode.set("DEMO", "WARNING")
        else:
            self.sidebar_mode.set("REEL", "INFO")

    def _view_label(self, key: str) -> str:
        for view_key, label, _view_class in self.view_specs:
            if view_key == key:
                return label
        return key

    def _show_notification_toast(self, title: str, message: str, severity: str) -> None:
        if self._tray_icon is None:
            return
        icon_type = {
            "HIGH": QSystemTrayIcon.MessageIcon.Warning,
            "CRITICAL": QSystemTrayIcon.MessageIcon.Critical,
        }.get(severity, QSystemTrayIcon.MessageIcon.Information)
        self._tray_icon.showMessage(title, message, icon_type, 4000)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._is_closing:
            event.accept()
            return

        self._is_closing = True
        self._poll_timer.stop()
        self._periodic_timer.stop()
        self._resize_timer.stop()

        app = QApplication.instance()
        if app is not None and self._usb_filter is not None:
            app.removeNativeEventFilter(self._usb_filter)
            self._usb_filter = None

        if self._tray_icon is not None:
            self._tray_icon.hide()

        for window in list(self._investigation_windows):
            window.close()
        self._investigation_windows.clear()

        try:
            self.controller.stop_services()
        except Exception:
            LOGGER.exception("Erreur pendant l'arret des services WireWall.")

        event.accept()


WireWallApp = WireWallMainWindow
