from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.theme import COLORS
from app.ui.views.base import BaseView
from app.ui.widgets.common import LabeledValue, ScrollableDetailText, ScrollableTree, SectionHeader, StatusPill
from app.utils.datetime import format_for_ui
from app.utils.ui import severity_color, shorten_text


class AlertsView(BaseView):
    view_title = "Alertes"

    ACK_OPTIONS = {
        "Toutes": "",
        "Non acquittees": "no",
        "Acquittees": "yes",
    }

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(2, weight=1)
        self._rows: dict[str, object] = {}
        self._selected_alert_key: str | None = None

        self.header = SectionHeader(
            self,
            "Centre d'alertes",
            "Lecture rapide des alertes critiques, suivi d'acquittement et recommandations.",
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        filters = ttk.LabelFrame(self, text="Filtres", style="Section.TLabelframe", padding=12)
        filters.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for column in range(4):
            filters.columnconfigure(column, weight=1 if column in {1, 3} else 0)
        self.severity_var = tk.StringVar(value="Toutes")
        self.ack_var = tk.StringVar(value="Toutes")
        ttk.Label(filters, text="Gravite").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.severity_combo = ttk.Combobox(
            filters,
            textvariable=self.severity_var,
            values=["Toutes", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
            state="readonly",
        )
        self.severity_combo.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(filters, text="Etat").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.ack_combo = ttk.Combobox(
            filters,
            textvariable=self.ack_var,
            values=list(self.ACK_OPTIONS.keys()),
            state="readonly",
        )
        self.ack_combo.grid(row=0, column=3, sticky="ew")
        ttk.Button(filters, text="Appliquer", command=self.refresh_data).grid(row=1, column=2, sticky="e", pady=(12, 0))
        ttk.Button(filters, text="Rafraichir", style="Accent.TButton", command=self.refresh_data).grid(
            row=1,
            column=3,
            sticky="e",
            pady=(12, 0),
        )
        self.severity_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_data())
        self.ack_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_data())

        list_frame = ttk.LabelFrame(self, text="Liste des alertes", style="Section.TLabelframe", padding=12)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        detail_frame = ttk.LabelFrame(self, text="Detail de l'alerte", style="Section.TLabelframe", padding=12)
        detail_frame.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(3, weight=1)

        self.table = ScrollableTree(list_frame, ("date", "severity", "title", "state", "score"), height=18)
        self.table.pack(fill="both", expand=True)
        for column, label, width in (
            ("date", "Date", 145),
            ("severity", "Gravite", 90),
            ("title", "Titre", 280),
            ("state", "Etat", 110),
            ("score", "Score", 70),
        ):
            self.table.tree.heading(column, text=label)
            self.table.tree.column(column, width=width, anchor="w")
        self.table.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_selected())
        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            self.table.tree.tag_configure(level, foreground=severity_color(level))
        self.table.tree.tag_configure("ACK", foreground=COLORS["muted"])

        top = ttk.Frame(detail_frame, style="Card.TFrame", padding=12)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="Statut", style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
        badge_row = ttk.Frame(top, style="CardInner.TFrame")
        badge_row.grid(row=0, column=1, sticky="e")
        self.severity_badge = StatusPill(badge_row, "AUCUNE", "INFO")
        self.severity_badge.pack(side="left")
        self.ack_badge = StatusPill(badge_row, "NON", "WARNING")
        self.ack_badge.pack(side="left", padx=(8, 0))

        metrics = ttk.Frame(detail_frame, style="Card.TFrame", padding=12)
        metrics.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        for column in range(2):
            metrics.columnconfigure(column, weight=1)
        self.values = {
            "title": LabeledValue(metrics, "Titre"),
            "date": LabeledValue(metrics, "Date"),
            "score": LabeledValue(metrics, "Score"),
            "device": LabeledValue(metrics, "Peripherique"),
        }
        self.values["title"].grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=6)
        self.values["date"].grid(row=0, column=1, sticky="ew", pady=6)
        self.values["score"].grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=6)
        self.values["device"].grid(row=1, column=1, sticky="ew", pady=6)

        actions = ttk.Frame(detail_frame)
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.ack_button = ttk.Button(actions, text="Acquitter l'alerte", style="Accent.TButton", command=self._acknowledge, state="disabled")
        self.ack_button.pack(side="left")

        self.detail_text = ScrollableDetailText(detail_frame, height=18)
        self.detail_text.grid(row=3, column=0, sticky="nsew")
        self._clear_selection_state()

    def refresh_data(self) -> None:
        severity = "" if self.severity_var.get() == "Toutes" else self.severity_var.get()
        acknowledged = self.ACK_OPTIONS[self.ack_var.get()]
        selected_key = self._get_selected_alert_key() or self._selected_alert_key
        alerts = self.controller.list_alerts(severity, acknowledged)
        self._rows.clear()
        self.table.clear()
        item_to_restore: str | None = None
        for alert in alerts:
            tags = [alert.severity]
            if alert.acknowledged:
                tags.append("ACK")
            item_id = self.table.tree.insert(
                "",
                "end",
                values=(
                    format_for_ui(alert.created_at),
                    alert.severity,
                    shorten_text(alert.title, 48),
                    "Acquittee" if alert.acknowledged else "A traiter",
                    alert.score,
                ),
                tags=tuple(tags),
            )
            self._rows[item_id] = alert
            if self._alert_key(alert) == selected_key:
                item_to_restore = item_id
        self.table.set_empty(bool(alerts), "Aucune alerte ne correspond aux filtres actifs.")
        if item_to_restore is not None:
            self.table.tree.selection_set(item_to_restore)
            self.table.tree.focus(item_to_restore)
            self.table.tree.see(item_to_restore)
            self._show_selected()
        else:
            self._clear_selection_state()

    def _selected_alert(self):
        selection = self.table.tree.selection()
        if not selection:
            return None
        return self._rows.get(selection[0])

    def _show_selected(self) -> None:
        alert = self._selected_alert()
        if alert is None:
            self._clear_selection_state()
            return
        self._selected_alert_key = self._alert_key(alert)
        self.severity_badge.set(alert.severity, alert.severity)
        self.ack_badge.set("ACQUITTEE" if alert.acknowledged else "ACTIVE", "OK" if alert.acknowledged else "WARNING")
        self.values["title"].set(alert.title)
        self.values["date"].set(format_for_ui(alert.created_at))
        self.values["score"].set(str(alert.score))
        self.values["device"].set(alert.device_key or "Aucun peripherique associe")
        self.detail_text.set_text(
            "Message :\n{message}\n\n"
            "Recommandations :\n- {recommendations}".format(
                message=alert.message,
                recommendations="\n- ".join(alert.recommendations or ["Aucune recommandation fournie."]),
            )
        )
        self.ack_button.configure(state="disabled" if alert.acknowledged else "normal")

    def _clear_selection_state(self) -> None:
        self._selected_alert_key = None
        self.severity_badge.set("AUCUNE", "INFO")
        self.ack_badge.set("AUCUNE", "INFO")
        for value in self.values.values():
            value.set("-")
        self.detail_text.set_text("Selectionnez une alerte pour consulter son detail et ses recommandations.")
        self.ack_button.configure(state="disabled")

    def _get_selected_alert_key(self) -> str | None:
        alert = self._selected_alert()
        if alert is None:
            return None
        return self._alert_key(alert)

    def _alert_key(self, alert) -> str:
        if alert.id is not None:
            return f"id:{alert.id}"
        return f"{alert.created_at}|{alert.title}|{alert.severity}"

    def _acknowledge(self) -> None:
        alert = self._selected_alert()
        if alert is None or alert.id is None:
            self.app.set_status("Selectionnez une alerte a acquitter.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.acknowledge_alert(alert.id),
            success_message="Alerte acquittee.",
            refresh=True,
        )
