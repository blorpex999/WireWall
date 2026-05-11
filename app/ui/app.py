from __future__ import annotations

import logging
import platform
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QCloseEvent, QIcon, QPixmap, QResizeEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
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
from app.ui.widgets.common import StatusBar, StatusPill
from app.utils.resources import asset_path
from app.utils.datetime import format_for_ui
from app.utils.ui import severity_color
from app.utils.windows import WindowsDeviceNotificationFilter
from app.version import __version__

LOGGER = logging.getLogger(__name__)


class NotificationHistoryDialog(QDialog):
    PERIODS = {
        "Derniere heure": "1h",
        "24h": "24h",
        "Semaine": "7d",
    }

    def __init__(self, parent: QWidget, controller: AppController) -> None:
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Notifications WireWall")
        self.resize(820, 520)
        self.setMinimumSize(680, 420)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)
        layout.addLayout(header)

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(3)
        header.addLayout(title_box, 1)

        title = QLabel("Notifications", self)
        title.setObjectName("title")
        title_box.addWidget(title)

        self.summary_label = QLabel("", self)
        self.summary_label.setObjectName("muted")
        title_box.addWidget(self.summary_label)

        self.period_filter = QComboBox(self)
        self.period_filter.addItems(self.PERIODS.keys())
        self.period_filter.setCurrentText("24h")
        self.period_filter.currentTextChanged.connect(lambda _value: self.refresh())
        header.addWidget(self.period_filter, 0, Qt.AlignmentFlag.AlignRight)

        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(["Heure", "Type", "Niveau", "Message"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.addStretch(1)
        refresh_button = QPushButton("Actualiser", self)
        refresh_button.setObjectName("subtle")
        refresh_button.clicked.connect(self.refresh)
        footer.addWidget(refresh_button)
        close_button = QPushButton("Fermer", self)
        close_button.clicked.connect(self.close)
        footer.addWidget(close_button)
        layout.addLayout(footer)

    def refresh(self) -> None:
        period = self.PERIODS.get(self.period_filter.currentText(), "24h")
        events = self.controller.list_notification_events(period)
        self.table.setRowCount(len(events))
        for row, event in enumerate(events):
            values = [
                format_for_ui(event.occurred_at),
                self._event_type_label(event.event_type),
                event.severity,
                event.summary,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                if column == 2:
                    item.setForeground(QColor(severity_color(event.severity)))
                self.table.setItem(row, column, item)
        self.summary_label.setText(f"{len(events)} notification(s) sur la periode selectionnee.")

    def _event_type_label(self, event_type: str) -> str:
        return {
            "connected": "Connexion",
            "disconnected": "Deconnexion",
            "scan_error": "Monitoring",
            "usb_attack_simulation_marker_detected": "Simulation",
        }.get(event_type, event_type.replace("_", " ").capitalize())


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
        self._notification_toasts: list[QFrame] = []
        self._notification_dialog: NotificationHistoryDialog | None = None
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
        root.setObjectName("app_root")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 12)
        root_layout.setSpacing(10)

        shell = QWidget(root)
        shell.setObjectName("app_shell")
        shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(10)
        root_layout.addWidget(shell, 1)

        self.sidebar = self._build_sidebar(shell)
        shell_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget(shell)
        self.stack.setObjectName("content_stack")
        self.stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
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
        self._refresh_notification_button()
        QTimer.singleShot(150, self._notify_view_resize)

    def _build_sidebar(self, parent: QWidget) -> QFrame:
        sidebar = QFrame(parent)
        sidebar.setObjectName("sidebar")
        sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sidebar.setFixedWidth(256)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QWidget(sidebar)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(2, 2, 2, 18)
        header_layout.setSpacing(12)
        layout.addWidget(header)

        logo_label = QLabel(header)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        logo_label.setFixedSize(52, 52)
        logo_pixmap = self._load_logo_pixmap()
        if logo_pixmap is not None:
            logo_label.setPixmap(logo_pixmap)
            header_layout.addWidget(logo_label, 0, Qt.AlignmentFlag.AlignTop)

        title_box = QWidget(header)
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        header_layout.addWidget(title_box, 1)

        title = QLabel("WireWall", title_box)
        title.setStyleSheet("font-size: 20pt; font-weight: 650;")
        title.setMinimumWidth(118)
        title_layout.addWidget(title)

        subtitle = QLabel("Surveillance USB Windows", title_box)
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        title_layout.addWidget(subtitle)

        self.sidebar_mode = StatusPill(title_box, "", "INFO")
        title_layout.addWidget(self.sidebar_mode, 0, Qt.AlignmentFlag.AlignLeft)

        self.demo_toggle = QCheckBox("Mode demo", sidebar)
        self.demo_toggle.setToolTip("Basculer entre les vrais peripheriques USB et un scenario USB simule.")
        self.demo_toggle.setChecked(self.controller.demo_mode)
        self.demo_toggle.toggled.connect(self._toggle_demo_mode)
        layout.addWidget(self.demo_toggle)

        self.notifications_button = QPushButton("Notifications", sidebar)
        self.notifications_button.setObjectName("subtle")
        self.notifications_button.setToolTip("Voir l'historique des notifications WireWall.")
        self.notifications_button.clicked.connect(self._show_notification_history)
        layout.addWidget(self.notifications_button)

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

    def _show_notification_history(self) -> None:
        if self._notification_dialog is None:
            self._notification_dialog = NotificationHistoryDialog(self, self.controller)
            self._notification_dialog.finished.connect(lambda _code: self._forget_notification_dialog())
        self._notification_dialog.refresh()
        self._notification_dialog.show()
        self._notification_dialog.raise_()
        self._notification_dialog.activateWindow()

    def _forget_notification_dialog(self) -> None:
        self._notification_dialog = None

    def _forget_investigation_window(self, window: QWidget) -> None:
        try:
            self._investigation_windows.remove(window)
        except ValueError:
            pass

    def set_status(self, message: str, level: str = "INFO") -> None:
        self.status_bar_widget.set_status(message, level)

    def refresh_mode_state(self, refresh_views: bool = False) -> None:
        self._refresh_mode_badges()
        if not refresh_views:
            return
        self._refresh_view("dashboard")
        if self.current_view_key is not None and self.current_view_key != "dashboard":
            self._refresh_view(self.current_view_key)
        self.request_repaint()

    def _toggle_demo_mode(self, checked: bool) -> None:
        self.demo_toggle.setEnabled(False)
        restart_requested = False
        try:
            target_settings = self.controller.set_demo_mode(checked)
            self.set_status(
                "Mode demo enregistre. Redemarrage de WireWall pour ouvrir la base demo."
                if target_settings.mode == "demo"
                else "Mode reel enregistre. Redemarrage de WireWall pour ouvrir la base reelle.",
                "WARNING" if target_settings.mode == "demo" else "OK",
            )
            restart_requested = True
            QTimer.singleShot(500, self._restart_application)
        except Exception:
            LOGGER.exception("Impossible de basculer le mode WireWall.")
            self.demo_toggle.blockSignals(True)
            self.demo_toggle.setChecked(self.controller.demo_mode)
            self.demo_toggle.blockSignals(False)
            self.set_status("Impossible de changer de mode.", "ERROR")
        finally:
            if not restart_requested:
                self.demo_toggle.setEnabled(True)

    def restart_for_mode_switch(self, target_mode: str) -> None:
        self.set_status(
            "Mode demo enregistre. Redemarrage de WireWall pour ouvrir la base demo."
            if target_mode == "demo"
            else "Mode reel enregistre. Redemarrage de WireWall pour ouvrir la base reelle.",
            "WARNING" if target_mode == "demo" else "OK",
        )
        QTimer.singleShot(500, self._restart_application)

    def _restart_application(self) -> None:
        launch_args = list(sys.argv[1:] if getattr(sys, "frozen", False) else sys.argv)
        if "--replace-existing" not in launch_args:
            launch_args.append("--replace-existing")
        try:
            subprocess.Popen([sys.executable, *launch_args], cwd=str(Path.cwd()))
        except Exception:
            LOGGER.exception("Impossible de relancer WireWall apres changement de mode.")
            self.set_status("Mode enregistre, mais relance automatique impossible. Relance WireWall manuellement.", "ERROR")
            return
        QApplication.quit()

    def _poll_backend_events(self) -> None:
        refresh_views: set[str] = set()
        for event in self.container.event_bus.drain():
            event_type = event["type"]
            if event_type == "device_event":
                payload = event["payload"]
                self.controller.request_brain_refresh()
                refresh_views.update({"dashboard", "devices", "history", "alerts"})
                self._refresh_notification_button()
                if payload.get("event_type") in {"connected", "disconnected"}:
                    self._notify_user(
                        payload.get("title", "Evenement appareil"),
                        payload.get("message", "Evenement appareil detecte."),
                        payload.get("severity", "INFO"),
                    )
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
                self._refresh_notification_button()
                self._notify_user(
                    payload.get("title", "Alerte WireWall"),
                    payload.get("message", "Nouvelle alerte."),
                    payload.get("severity", "WARNING"),
                )
            elif event_type == "monitor_error":
                message = event["payload"].get("message", "Erreur de monitoring.")
                self.set_status(message, "ERROR")
                self._notify_user("Erreur de monitoring", message, "ERROR")
                self._refresh_notification_button()
                refresh_views.add("dashboard")
            elif event_type == "monitor_warning":
                message = event["payload"].get("message", "Degradation du monitoring USB.")
                self.set_status(message, "WARNING")
                self._notify_user("Attention WireWall", message, "WARNING")
                self._refresh_notification_button()
                refresh_views.add("dashboard")
            elif event_type == "background_task_error":
                message = event["payload"].get("message", "Erreur de tache de fond.")
                self.set_status(message, "ERROR")
                self._notify_user("Erreur de tache de fond", message, "ERROR")
                self._refresh_notification_button()
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
        if self._notification_dialog is not None and self._notification_dialog.isVisible():
            self._notification_dialog.refresh()

    def _refresh_notification_button(self) -> None:
        if not hasattr(self, "notifications_button"):
            return
        count = len(self.controller.list_notification_events("24h"))
        self.notifications_button.setText(f"Notifications ({count})" if count else "Notifications")

    def _refresh_view(self, key: str) -> None:
        try:
            self.views[key].refresh_preserving_scroll()
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
        QTimer.singleShot(16, self._force_repaint)

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
        self._position_notification_toasts()
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
        demo_mode = self.controller.demo_mode
        self.sidebar_mode.set("DEMO" if demo_mode else "REEL", "WARNING" if demo_mode else "INFO")
        self.status_bar_widget.set_mode(demo_mode)
        if hasattr(self, "demo_toggle"):
            self.demo_toggle.blockSignals(True)
            self.demo_toggle.setChecked(demo_mode)
            self.demo_toggle.blockSignals(False)

    def _view_label(self, key: str) -> str:
        for view_key, label, _view_class in self.view_specs:
            if view_key == key:
                return label
        return key

    def _notify_user(self, title: str, message: str, severity: str) -> None:
        self._show_in_app_toast(title, message, severity)
        if self.controller.settings.desktop_notifications_enabled:
            self._show_notification_toast(title, message, severity)

    def _show_notification_toast(self, title: str, message: str, severity: str) -> None:
        if self._tray_icon is None:
            return
        icon_type = {
            "WARNING": QSystemTrayIcon.MessageIcon.Warning,
            "ERROR": QSystemTrayIcon.MessageIcon.Critical,
            "HIGH": QSystemTrayIcon.MessageIcon.Warning,
            "CRITICAL": QSystemTrayIcon.MessageIcon.Critical,
        }.get(severity, QSystemTrayIcon.MessageIcon.Information)
        self._tray_icon.showMessage(title, message, icon_type, 4000)

    def _show_in_app_toast(self, title: str, message: str, severity: str) -> None:
        parent = self.centralWidget()
        if parent is None:
            return
        toast = QFrame(parent)
        toast.setObjectName("notification_toast")
        toast.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        toast.setFixedWidth(390)
        tone = {
            "OK": ("#123b2a", "#2ee59d"),
            "LOW": ("#142331", "#7fb4ff"),
            "INFO": ("#142331", "#7fb4ff"),
            "MEDIUM": ("#3a2f10", "#ffd166"),
            "WARNING": ("#3a2f10", "#ffd166"),
            "HIGH": ("#3a1d12", "#ff9f66"),
            "ERROR": ("#3b1420", "#ff5f7a"),
            "CRITICAL": ("#3b1420", "#ff5f7a"),
        }.get(str(severity).upper(), ("#142331", "#7fb4ff"))
        toast.setStyleSheet(
            f"""
            QFrame#notification_toast {{
                background-color: {tone[0]};
                border: 1px solid {tone[1]};
                border-radius: 8px;
            }}
            QLabel#toast_title {{
                color: #f8fafc;
                font-weight: 700;
                font-size: 10pt;
            }}
            QLabel#toast_message {{
                color: #d7e3ea;
                font-size: 9pt;
            }}
            """
        )
        layout = QVBoxLayout(toast)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        title_label = QLabel(title, toast)
        title_label.setObjectName("toast_title")
        title_label.setWordWrap(True)
        message_label = QLabel(message, toast)
        message_label.setObjectName("toast_message")
        message_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        toast.adjustSize()
        toast.setMinimumHeight(max(72, toast.sizeHint().height()))
        toast.show()
        toast.raise_()
        self._notification_toasts.append(toast)
        self._position_notification_toasts()
        QTimer.singleShot(5200, lambda current=toast: self._dismiss_in_app_toast(current))

    def _dismiss_in_app_toast(self, toast: QFrame) -> None:
        if toast in self._notification_toasts:
            self._notification_toasts.remove(toast)
        toast.deleteLater()
        self._position_notification_toasts()

    def _position_notification_toasts(self) -> None:
        parent = self.centralWidget()
        if parent is None:
            return
        margin = 18
        y = margin
        for toast in list(self._notification_toasts):
            if toast.parent() is None:
                self._notification_toasts.remove(toast)
                continue
            x = max(margin, parent.width() - toast.width() - margin)
            toast.move(x, y)
            y += toast.height() + 10

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

        for toast in list(self._notification_toasts):
            toast.deleteLater()
        self._notification_toasts.clear()

        for window in list(self._investigation_windows):
            window.close()
        self._investigation_windows.clear()

        try:
            self.controller.stop_services()
        except Exception:
            LOGGER.exception("Erreur pendant l'arret des services WireWall.")

        event.accept()


WireWallApp = WireWallMainWindow
