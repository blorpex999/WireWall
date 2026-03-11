from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app.ui.views.base import BaseView
from app.ui.widgets.common import ScrollableTree, SectionHeader, StatusPill
from app.utils.ui import match_type_text, policy_type_text, shorten_text


class PoliciesView(BaseView):
    view_title = "Regles USB"

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.tables: dict[str, ScrollableTree] = {}
        self.row_maps: dict[str, dict[str, object]] = {"whitelist": {}, "blacklist": {}}

        self.header = SectionHeader(
            self,
            "Regles USB",
            "Gestion separee des listes blanche et noire, import/export et regles cibles.",
        )
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        controls = ttk.LabelFrame(self, text="Recherche et echanges", style="Section.TLabelframe", padding=12)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="Recherche").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.query_var = tk.StringVar()
        self.query_entry = ttk.Entry(controls, textvariable=self.query_var)
        self.query_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Button(controls, text="Appliquer", command=self.refresh_data).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(controls, text="Importer", command=self._import).grid(row=0, column=3, padx=(0, 8))
        ttk.Button(controls, text="Exporter", style="Accent.TButton", command=self._export).grid(row=0, column=4)
        self.query_var.trace_add("write", lambda *_args: self.schedule_refresh(250))
        self.query_entry.bind("<Return>", lambda _event: self.refresh_data())

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=0, sticky="nsew")
        self.tabs = {}
        for policy_type in ("whitelist", "blacklist"):
            tab = ttk.Frame(self.notebook, padding=12)
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(1, weight=1)
            self.notebook.add(tab, text=policy_type_text(policy_type))
            self.tabs[policy_type] = tab
            self._build_policy_tab(tab, policy_type)

        self.notebook.bind("<<NotebookTabChanged>>", lambda _event: self._sync_form_target())

        form = ttk.LabelFrame(self, text="Ajouter une regle", style="Section.TLabelframe", padding=12)
        form.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        for column in range(5):
            form.columnconfigure(column, weight=1 if column in {1, 2, 3, 4} else 0)
        ttk.Label(form, text="Cible").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.target_badge = StatusPill(form, "", "OK")
        self.target_badge.grid(row=0, column=1, sticky="w")
        ttk.Label(form, text="Type de match").grid(row=1, column=0, sticky="w", pady=(12, 0), padx=(0, 8))
        self.new_match = tk.StringVar(value="VID:PID")
        ttk.Combobox(
            form,
            textvariable=self.new_match,
            values=["VID:PID", "Numero de serie"],
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", pady=(12, 0), padx=(0, 12))
        ttk.Label(form, text="Valeur").grid(row=1, column=2, sticky="w", pady=(12, 0), padx=(0, 8))
        self.new_value = tk.StringVar()
        ttk.Entry(form, textvariable=self.new_value).grid(row=1, column=3, sticky="ew", pady=(12, 0), padx=(0, 12))
        ttk.Label(form, text="Label").grid(row=2, column=0, sticky="w", pady=(12, 0), padx=(0, 8))
        self.new_label = tk.StringVar()
        ttk.Entry(form, textvariable=self.new_label).grid(row=2, column=1, columnspan=2, sticky="ew", pady=(12, 0), padx=(0, 12))
        ttk.Label(form, text="Notes").grid(row=2, column=3, sticky="w", pady=(12, 0), padx=(0, 8))
        self.new_notes = tk.StringVar()
        ttk.Entry(form, textvariable=self.new_notes).grid(row=2, column=4, sticky="ew", pady=(12, 0))
        self.add_button = ttk.Button(form, text="", style="Accent.TButton", command=self._add_policy)
        self.add_button.grid(row=3, column=4, sticky="e", pady=(16, 0))
        self._sync_form_target()

    def refresh_data(self) -> None:
        query = self.query_var.get().strip()
        for policy_type in ("whitelist", "blacklist"):
            entries = self.controller.list_policies(policy_type, query)
            self.row_maps[policy_type].clear()
            table = self.tables[policy_type]
            table.clear()
            for entry in entries:
                item_id = table.tree.insert(
                    "",
                    "end",
                    values=(match_type_text(entry.match_type), entry.value, shorten_text(entry.label, 36), shorten_text(entry.notes, 52)),
                )
                self.row_maps[policy_type][item_id] = entry
            table.set_empty(bool(entries), f"Aucune regle {policy_type_text(policy_type).lower()} pour ce filtre.")
            self.notebook.tab(self.tabs[policy_type], text=f"{policy_type_text(policy_type)} ({len(entries)})")

    def _build_policy_tab(self, tab, policy_type: str) -> None:
        top = ttk.Frame(tab, style="Card.TFrame", padding=12)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text=f"{policy_type_text(policy_type)} active", style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
        tone = "OK" if policy_type == "whitelist" else "CRITICAL"
        badge = StatusPill(top, policy_type_text(policy_type).upper(), tone)
        badge.grid(row=0, column=1, sticky="e")
        ttk.Button(top, text="Supprimer la selection", style="Subtle.TButton", command=lambda value=policy_type: self._delete_policy(value)).grid(
            row=1,
            column=1,
            sticky="e",
            pady=(10, 0),
        )

        table = ScrollableTree(tab, ("match", "value", "label", "notes"), height=12)
        table.grid(row=1, column=0, sticky="nsew")
        for column, label, width in (
            ("match", "Match", 150),
            ("value", "Valeur", 220),
            ("label", "Label", 240),
            ("notes", "Notes", 340),
        ):
            table.tree.heading(column, text=label)
            table.tree.column(column, width=width, anchor="w")
        self.tables[policy_type] = table

    def _current_policy_type(self) -> str:
        selected = self.notebook.select()
        for policy_type, frame in self.tabs.items():
            if str(frame) == selected:
                return policy_type
        return "whitelist"

    def _sync_form_target(self) -> None:
        policy_type = self._current_policy_type()
        tone = "OK" if policy_type == "whitelist" else "CRITICAL"
        self.target_badge.set(policy_type_text(policy_type).upper(), tone)
        self.add_button.configure(text=f"Ajouter a la {policy_type_text(policy_type).lower()}")

    def _add_policy(self) -> None:
        policy_type = self._current_policy_type()
        match_type = "vid_pid" if self.new_match.get() == "VID:PID" else "serial"
        self.run_action(
            lambda: self.controller.add_policy(
                policy_type,
                match_type,
                self.new_value.get().strip(),
                self.new_label.get().strip(),
                self.new_notes.get().strip(),
            ),
            success_message=f"Regle ajoutee a la {policy_type_text(policy_type).lower()}.",
            refresh=True,
        )

    def _delete_policy(self, policy_type: str) -> None:
        table = self.tables[policy_type].tree
        selection = table.selection()
        if not selection:
            self.app.set_status("Selectionnez une regle a supprimer.", "WARNING")
            return
        entry = self.row_maps[policy_type].get(selection[0])
        if entry is None or entry.id is None:
            return
        if not messagebox.askyesno("Confirmation", f"Supprimer cette regle de {policy_type_text(policy_type).lower()} ?"):
            return
        self.run_action(
            lambda: self.controller.remove_policy(entry.id),
            success_message="Regle supprimee.",
            refresh=True,
        )

    def _import(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Regles USB", "*.json *.csv"), ("JSON", "*.json"), ("CSV", "*.csv")])
        if not path:
            return
        self.run_action(
            lambda: self.controller.import_policies(path),
            success_message=lambda count: f"{count} regle(s) importee(s) depuis {path}.",
            refresh=True,
        )

    def _export(self) -> None:
        default_path = Path(self.controller.settings.export_directory) / "wirewall_policies.json"
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=default_path.name,
            initialdir=str(default_path.parent),
            filetypes=[("JSON", "*.json"), ("CSV", "*.csv")],
        )
        if not path:
            return
        self.run_action(
            lambda: self.controller.export_policies(path),
            success_message=lambda target: f"Regles exportees : {target}",
        )
