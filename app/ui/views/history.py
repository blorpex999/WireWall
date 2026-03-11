from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.views.base import BaseView
from app.ui.widgets.common import LabeledValue, ScrollableDetailText, ScrollableTree, SectionHeader, StatusPill
from app.utils.datetime import format_for_ui
from app.utils.ui import severity_color, shorten_text


class HistoryView(BaseView):
    view_title = "Historique"

    SEVERITY_OPTIONS = {
        "Toutes": "",
        "INFO": "INFO",
        "LOW": "LOW",
        "MEDIUM": "MEDIUM",
        "HIGH": "HIGH",
        "CRITICAL": "CRITICAL",
        "WARNING": "WARNING",
        "ERROR": "ERROR",
    }

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(2, weight=1)
        self._rows: dict[str, object] = {}
        self._selected_event_key: str | None = None

        self.header = SectionHeader(
            self,
            "Historique et audit",
            "Trace horodatee des evenements USB, des anomalies de scan et des exports d'audit.",
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        toolbar = ttk.LabelFrame(self, text="Filtres et exports", style="Section.TLabelframe", padding=12)
        toolbar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        toolbar.columnconfigure(1, weight=1)
        toolbar.columnconfigure(3, weight=1)
        ttk.Label(toolbar, text="Recherche").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(toolbar, text="Gravite").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.severity_var = tk.StringVar(value="Toutes")
        self.severity_combo = ttk.Combobox(
            toolbar,
            textvariable=self.severity_var,
            values=list(self.SEVERITY_OPTIONS.keys()),
            state="readonly",
        )
        self.severity_combo.grid(row=0, column=3, sticky="ew")
        ttk.Button(toolbar, text="Appliquer", command=self.refresh_data).grid(row=1, column=2, sticky="e", pady=(12, 0))
        actions = ttk.Frame(toolbar)
        actions.grid(row=1, column=3, sticky="e", pady=(12, 0))
        ttk.Button(actions, text="CSV", command=lambda: self._export("csv")).pack(side="left")
        ttk.Button(actions, text="JSON", command=lambda: self._export("json")).pack(side="left", padx=8)
        ttk.Button(actions, text="Rapport HTML", style="Accent.TButton", command=lambda: self._export("html")).pack(side="left")
        self.search_var.trace_add("write", lambda *_args: self.schedule_refresh(250))
        self.search_entry.bind("<Return>", lambda _event: self.refresh_data())
        self.severity_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_data())

        list_frame = ttk.LabelFrame(self, text="Evenements", style="Section.TLabelframe", padding=12)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        detail_frame = ttk.LabelFrame(self, text="Detail d'audit", style="Section.TLabelframe", padding=12)
        detail_frame.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(3, weight=1)

        self.table = ScrollableTree(list_frame, ("date", "type", "device", "summary", "severity"), height=18)
        self.table.pack(fill="both", expand=True)
        for column, label, width in (
            ("date", "Date", 150),
            ("type", "Type", 110),
            ("device", "Peripherique", 230),
            ("summary", "Resume", 320),
            ("severity", "Gravite", 95),
        ):
            self.table.tree.heading(column, text=label)
            self.table.tree.column(column, width=width, anchor="w")
        self.table.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_selected())
        for tone in ("LOW", "MEDIUM", "HIGH", "CRITICAL", "INFO", "WARNING", "ERROR"):
            self.table.tree.tag_configure(tone, foreground=severity_color(tone))

        top = ttk.Frame(detail_frame, style="Card.TFrame", padding=12)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="Resume de l'evenement", style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
        self.severity_badge = StatusPill(top, "INFO", "INFO")
        self.severity_badge.grid(row=0, column=1, sticky="e")

        metrics = ttk.Frame(detail_frame, style="Card.TFrame", padding=12)
        metrics.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        for column in range(2):
            metrics.columnconfigure(column, weight=1)
        self.values = {
            "date": LabeledValue(metrics, "Date"),
            "type": LabeledValue(metrics, "Type"),
            "source": LabeledValue(metrics, "Source"),
            "device": LabeledValue(metrics, "Peripherique"),
            "score": LabeledValue(metrics, "Score"),
            "level": LabeledValue(metrics, "Niveau"),
        }
        placements = [
            ("date", 0, 0),
            ("type", 0, 1),
            ("source", 1, 0),
            ("device", 1, 1),
            ("score", 2, 0),
            ("level", 2, 1),
        ]
        for key, row, column in placements:
            self.values[key].grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0), pady=6)

        self.detail_text = ScrollableDetailText(detail_frame, height=18)
        self.detail_text.grid(row=3, column=0, sticky="nsew")
        self._clear_selection_state()

    def refresh_data(self) -> None:
        severity = self.SEVERITY_OPTIONS[self.severity_var.get()]
        selected_key = self._get_selected_event_key() or self._selected_event_key
        events = self.controller.list_events(self.search_var.get().strip(), severity)
        self._rows.clear()
        self.table.clear()
        item_to_restore: str | None = None
        for event in events:
            item_id = self.table.tree.insert(
                "",
                "end",
                values=(
                    format_for_ui(event.occurred_at),
                    event.event_type,
                    shorten_text(event.device_key or "-", 28),
                    shorten_text(event.summary, 60),
                    event.severity,
                ),
                tags=(event.severity,),
            )
            self._rows[item_id] = event
            if self._event_key(event) == selected_key:
                item_to_restore = item_id
        self.table.set_empty(bool(events), "Aucun evenement a afficher avec les filtres actuels.")
        if item_to_restore is not None:
            self.table.tree.selection_set(item_to_restore)
            self.table.tree.focus(item_to_restore)
            self.table.tree.see(item_to_restore)
            self._show_selected()
        else:
            self._clear_selection_state()

    def _show_selected(self) -> None:
        selection = self.table.tree.selection()
        if not selection:
            self._clear_selection_state()
            return
        event = self._rows.get(selection[0])
        if event is None:
            self._clear_selection_state()
            return
        self._selected_event_key = self._event_key(event)
        self.severity_badge.set(event.severity, event.severity)
        self.values["date"].set(format_for_ui(event.occurred_at))
        self.values["type"].set(event.event_type)
        self.values["source"].set(event.source)
        self.values["device"].set(event.device_key or "Aucun")
        self.values["score"].set(str(event.score))
        self.values["level"].set(event.level)
        self.detail_text.set_text(
            "Resume :\n{summary}\n\n"
            "Raisons :\n- {reasons}\n\n"
            "Payload :\n{payload}".format(
                summary=event.summary,
                reasons="\n- ".join(event.reasons or ["Aucune raison fournie."]),
                payload=event.payload,
            )
        )

    def _clear_selection_state(self) -> None:
        self._selected_event_key = None
        self.severity_badge.set("INFO", "INFO")
        for value in self.values.values():
            value.set("-")
        self.detail_text.set_text("Selectionnez un evenement pour afficher son contexte d'audit detaille.")

    def _get_selected_event_key(self) -> str | None:
        selection = self.table.tree.selection()
        if not selection:
            return None
        event = self._rows.get(selection[0])
        if event is None:
            return None
        return self._event_key(event)

    def _event_key(self, event) -> str:
        if event.id is not None:
            return f"id:{event.id}"
        return f"{event.occurred_at}|{event.event_type}|{event.device_key or ''}"

    def _export(self, fmt: str) -> None:
        self.run_action(
            lambda: self.controller.export_report(fmt),
            success_message=lambda target: f"Export {fmt.upper()} genere : {target}",
        )
