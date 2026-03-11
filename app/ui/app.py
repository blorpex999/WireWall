from __future__ import annotations

import ctypes
import tkinter as tk
from tkinter import ttk

from app.ui.controller import AppController
from app.ui.theme import apply_dark_theme
from app.ui.views.about import AboutView
from app.ui.views.ai_analysis import AIAnalysisView
from app.ui.views.alerts import AlertsView
from app.ui.views.dashboard import DashboardView
from app.ui.views.devices import DevicesView
from app.ui.views.history import HistoryView
from app.ui.views.policies import PoliciesView
from app.ui.views.settings import SettingsView
from app.ui.views.usb_control import USBControlView
from app.ui.widgets.common import DemoBanner, StatusBar, StatusPill
from app.utils.windows import WindowsDeviceNotificationHook
from app.version import __version__


class WireWallApp(tk.Tk):
    def __init__(self, container) -> None:
        super().__init__()
        self.title(f"WireWall {__version__}")
        self.geometry("1450x920")
        self.minsize(1180, 780)
        apply_dark_theme(self)

        self.container = container
        self.controller = AppController(container)
        self.hook = WindowsDeviceNotificationHook()
        self.nav_buttons: dict[str, ttk.Button] = {}
        self._repaint_scheduled = False

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self.banner = DemoBanner(self, visible=self.controller.demo_mode)
        if self.controller.demo_mode:
            self.banner.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(14, 0))

        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding=16)
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=(14, 8), pady=14)
        self.sidebar.columnconfigure(0, weight=1)

        header = ttk.Frame(self.sidebar, style="SidebarHeader.TFrame", padding=(4, 2, 4, 16))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="WireWall", style="NavTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Surveillance USB Windows", style="NavSubTitle.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 6))
        self.sidebar_mode = StatusPill(header, "", "INFO")
        self.sidebar_mode.grid(row=0, column=1, rowspan=2, sticky="e")
        self._refresh_mode_badges()

        self.content = ttk.Frame(self, padding=(0, 14, 14, 0))
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 14))
        self.status_bar.set_mode(self.controller.demo_mode)

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
        self.views = {key: view_class(self.content, self.controller, self) for key, _label, view_class in self.view_specs}
        self.current_view_key: str | None = None

        for index, (key, label, _view_class) in enumerate(self.view_specs, start=1):
            button = ttk.Button(
                self.sidebar,
                text=label,
                style="Sidebar.TButton",
                command=lambda value=key: self.show_view(value),
            )
            button.grid(row=index, column=0, sticky="ew", pady=4)
            self.nav_buttons[key] = button

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(150, self._attach_hook)
        self.after(250, self._poll_backend_events)
        self.after(max(1500, self.controller.settings.dashboard_refresh_ms), self._periodic_refresh)

        self.controller.start_services()
        self.show_view("dashboard")
        self.controller.request_health_refresh()
        self.controller.request_brain_refresh()
        self.set_status("WireWall initialise.", "OK")

    def show_view(self, name: str) -> None:
        if self.current_view_key is not None:
            self.views[self.current_view_key].grid_forget()
        view = self.views[name]
        view.grid(row=0, column=0, sticky="nsew")
        view.refresh_data()
        self.current_view_key = name
        self._refresh_nav_state()
        self.title(f"WireWall {__version__} - {self._view_label(name)}")
        self.set_status(f"Vue active : {self._view_label(name)}", "INFO")
        self.request_repaint()

    def set_status(self, message: str, level: str = "INFO") -> None:
        self.status_bar.set_status(message, level)
        self.request_repaint()

    def _attach_hook(self) -> None:
        self.update_idletasks()
        attached = self.hook.attach(self, lambda _reason, _code: self.after_idle(self.controller.refresh_monitor))
        if attached:
            self.set_status("Hook Windows USB attache.", "INFO")

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

        if "dashboard" in refresh_views:
            self.views["dashboard"].refresh_data()
        if self.current_view_key is not None and self.current_view_key != "dashboard" and self.current_view_key in refresh_views:
            self.views[self.current_view_key].refresh_data()
        if refresh_views:
            self.request_repaint()
        self.after(250, self._poll_backend_events)

    def _periodic_refresh(self) -> None:
        self.controller.request_health_refresh()
        self.after(max(1500, self.controller.settings.dashboard_refresh_ms), self._periodic_refresh)

    def _refresh_nav_state(self) -> None:
        for key, button in self.nav_buttons.items():
            button.configure(style="SidebarActive.TButton" if key == self.current_view_key else "Sidebar.TButton")

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

    def _on_close(self) -> None:
        self.hook.detach()
        self.controller.stop_services()
        self.destroy()

    def request_repaint(self) -> None:
        if self._repaint_scheduled:
            return
        self._repaint_scheduled = True
        self.after_idle(self._force_repaint)

    def _force_repaint(self) -> None:
        self._repaint_scheduled = False
        try:
            self.update_idletasks()
            if self.winfo_exists() and self.tk.call("tk", "windowingsystem") == "win32":
                flags = 0x0001 | 0x0004 | 0x0080 | 0x0100
                ctypes.windll.user32.RedrawWindow(self.winfo_id(), None, None, flags)
        except Exception:
            pass
