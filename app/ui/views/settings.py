from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.views.base import BaseView
from app.ui.widgets.common import ScrollablePage, SectionHeader


class SettingsView(BaseView):
    view_title = "Parametres"

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.page = ScrollablePage(self)
        self.page.grid(row=0, column=0, sticky="nsew")
        self.content = self.page.body
        self.content.columnconfigure(0, weight=1)
        self.content.columnconfigure(1, weight=1)

        self.header = SectionHeader(
            self.content,
            "Parametres",
            "Reglage du monitoring, de la retention, du profil de securite, des suggestions et de l'integration Ollama.",
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        self.vars = {
            "scan_interval_seconds": tk.StringVar(),
            "history_retention_days": tk.StringVar(),
            "log_level": tk.StringVar(),
            "ollama_base_url": tk.StringVar(),
            "ollama_model": tk.StringVar(),
            "ollama_timeout_seconds": tk.StringVar(),
            "security_profile": tk.StringVar(),
            "export_directory": tk.StringVar(),
            "recommendation_mode": tk.StringVar(),
        }
        self.bool_vars = {
            "autostart_enabled": tk.BooleanVar(value=False),
            "desktop_notifications_enabled": tk.BooleanVar(value=True),
        }

        monitoring = ttk.LabelFrame(self.content, text="Monitoring", style="Section.TLabelframe", padding=16)
        monitoring.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        monitoring.columnconfigure(1, weight=1)
        self._add_entry_field(monitoring, 0, "Frequence de scan (s)", "scan_interval_seconds")
        self._add_combo_field(monitoring, 1, "Profil de securite", "security_profile", ["Normal", "Strict", "Presentation"])
        ttk.Checkbutton(
            monitoring,
            text="Activer le demarrage avec Windows",
            variable=self.bool_vars["autostart_enabled"],
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(14, 0))

        audit = ttk.LabelFrame(self.content, text="Audit, alertes et suggestions", style="Section.TLabelframe", padding=16)
        audit.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        audit.columnconfigure(1, weight=1)
        self._add_entry_field(audit, 0, "Retention historique (jours)", "history_retention_days")
        self._add_combo_field(audit, 1, "Niveau de logs", "log_level", ["DEBUG", "INFO", "WARNING", "ERROR"])
        self._add_combo_field(audit, 2, "Mode recommandations", "recommendation_mode", ["conservative", "balanced", "proactive"])
        ttk.Checkbutton(
            audit,
            text="Notifications locales des alertes HIGH / CRITICAL",
            variable=self.bool_vars["desktop_notifications_enabled"],
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(14, 0))

        ollama = ttk.LabelFrame(self.content, text="IA locale Ollama", style="Section.TLabelframe", padding=16)
        ollama.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        ollama.columnconfigure(1, weight=1)
        self._add_entry_field(ollama, 0, "URL locale", "ollama_base_url")
        self._add_entry_field(ollama, 1, "Modele", "ollama_model")
        self._add_entry_field(ollama, 2, "Timeout (s)", "ollama_timeout_seconds")

        paths = ttk.LabelFrame(self.content, text="Chemins", style="Section.TLabelframe", padding=16)
        paths.grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        paths.columnconfigure(1, weight=1)
        self._add_entry_field(paths, 0, "Dossier des exports", "export_directory")
        ttk.Label(paths, text="Base SQLite", style="Muted.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=(12, 0))
        self.db_path_var = tk.StringVar()
        ttk.Label(paths, textvariable=self.db_path_var, style="Muted.TLabel", wraplength=420, justify="left").grid(
            row=1,
            column=1,
            sticky="w",
            pady=(12, 0),
        )

        footer = ttk.Frame(self.content, style="Card.TFrame", padding=16)
        footer.grid(row=3, column=0, columnspan=2, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(
            footer,
            text="Les changements prennent effet au prochain cycle de monitoring, au prochain rapport et au prochain appel Ollama.",
            style="CardMuted.TLabel",
            wraplength=980,
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Enregistrer les parametres", style="Accent.TButton", command=self._save).grid(
            row=0,
            column=1,
            sticky="e",
        )

    def on_host_resize(self, width: int, height: int) -> None:
        self.after_idle(self.page._on_body_configure, None)

    def reset_scroll_position(self) -> None:
        self.page.scroll_to_top()

    def refresh_data(self) -> None:
        settings = self.controller.settings
        for field_name, variable in self.vars.items():
            variable.set(str(getattr(settings, field_name)))
        for field_name, variable in self.bool_vars.items():
            variable.set(bool(getattr(settings, field_name)))
        self.db_path_var.set(str(self.controller.get_database_path()))

    def _save(self) -> None:
        values = {key: variable.get() for key, variable in self.vars.items()}
        values.update({key: variable.get() for key, variable in self.bool_vars.items()})
        self.run_action(
            lambda: self.controller.save_settings(values),
            success_message=self._success_message,
            refresh=True,
        )

    def _success_message(self, settings) -> str:
        notice = self.controller.consume_settings_notice()
        base_message = f"Parametres enregistres. Profil actif : {settings.security_profile}"
        if notice is None:
            return base_message
        return f"{base_message} | {notice[0]}"

    def _add_entry_field(self, master, row: int, label: str, var_name: str) -> None:
        ttk.Label(master, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=(0 if row == 0 else 12, 0))
        ttk.Entry(master, textvariable=self.vars[var_name]).grid(row=row, column=1, sticky="ew", pady=(0 if row == 0 else 12, 0))

    def _add_combo_field(self, master, row: int, label: str, var_name: str, values: list[str]) -> None:
        ttk.Label(master, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=(0 if row == 0 else 12, 0))
        ttk.Combobox(master, textvariable=self.vars[var_name], values=values, state="readonly").grid(
            row=row,
            column=1,
            sticky="ew",
            pady=(0 if row == 0 else 12, 0),
        )
