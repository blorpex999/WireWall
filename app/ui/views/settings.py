from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.views.base import BaseView
from app.ui.widgets.common import SectionHeader


class SettingsView(BaseView):
    view_title = "Parametres"

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.header = SectionHeader(
            self,
            "Parametres",
            "Reglage du monitoring, de la retention, du profil de securite et de l'integration Ollama.",
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
        }

        monitoring = ttk.LabelFrame(self, text="Monitoring", style="Section.TLabelframe", padding=16)
        monitoring.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        monitoring.columnconfigure(1, weight=1)
        self._add_entry_field(monitoring, 0, "Frequence de scan (s)", "scan_interval_seconds")
        self._add_combo_field(monitoring, 1, "Profil de securite", "security_profile", ["Normal", "Strict", "Presentation"])

        audit = ttk.LabelFrame(self, text="Audit et logs", style="Section.TLabelframe", padding=16)
        audit.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        audit.columnconfigure(1, weight=1)
        self._add_entry_field(audit, 0, "Retention historique (jours)", "history_retention_days")
        self._add_combo_field(audit, 1, "Niveau de logs", "log_level", ["DEBUG", "INFO", "WARNING", "ERROR"])

        ollama = ttk.LabelFrame(self, text="IA locale Ollama", style="Section.TLabelframe", padding=16)
        ollama.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        ollama.columnconfigure(1, weight=1)
        self._add_entry_field(ollama, 0, "URL locale", "ollama_base_url")
        self._add_entry_field(ollama, 1, "Modele", "ollama_model")
        self._add_entry_field(ollama, 2, "Timeout (s)", "ollama_timeout_seconds")

        paths = ttk.LabelFrame(self, text="Chemins", style="Section.TLabelframe", padding=16)
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

        footer = ttk.Frame(self, style="Card.TFrame", padding=16)
        footer.grid(row=3, column=0, columnspan=2, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(
            footer,
            text="Les changements prennent effet sur le prochain cycle de monitoring ou sur le prochain appel Ollama.",
            style="Muted.TLabel",
            wraplength=980,
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Enregistrer les parametres", style="Accent.TButton", command=self._save).grid(
            row=0,
            column=1,
            sticky="e",
        )

    def refresh_data(self) -> None:
        settings = self.controller.settings
        for field_name, variable in self.vars.items():
            variable.set(str(getattr(settings, field_name)))
        self.db_path_var.set(str(self.controller.get_database_path()))

    def _save(self) -> None:
        self.run_action(
            lambda: self.controller.save_settings({key: variable.get() for key, variable in self.vars.items()}),
            success_message=lambda settings: f"Parametres enregistres. Profil actif : {settings.security_profile}",
            refresh=True,
        )

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
