from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.views.base import BaseView
from app.ui.widgets.common import LabeledValue, ScrollableDetailText, ScrollableTree, SectionHeader, StatusPill
from app.utils.datetime import format_for_ui
from app.utils.ui import (
    category_text,
    decision_text,
    device_status_text,
    severity_color,
    shorten_text,
    trust_state_text,
    trust_state_tone,
)


class DevicesView(BaseView):
    view_title = "Peripheriques"

    CATEGORY_OPTIONS = {
        "Toutes les categories": "",
        "Stockage": "storage",
        "HID": "hid",
        "Hub": "hub",
        "Imagerie": "imaging",
        "Communication": "communication",
        "Specifique constructeur": "vendor_specific",
        "Inconnu": "unknown",
    }
    STATUS_OPTIONS = {
        "Tous les statuts": "",
        "Connecte": "connected",
        "Deconnecte": "disconnected",
    }

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(2, weight=1)
        self._rows: dict[str, object] = {}
        self._selected_device_key: str | None = None

        self.header = SectionHeader(
            self,
            "Peripheriques USB",
            "Inventaire actif, contexte de confiance et actions de policy sur les equipements observes.",
            "MODE DEMO" if self.controller.demo_mode else "MODE REEL",
            "WARNING" if self.controller.demo_mode else "INFO",
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        filters = ttk.LabelFrame(self, text="Filtres et actions", style="Section.TLabelframe", padding=12)
        filters.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for column in range(6):
            filters.columnconfigure(column, weight=1 if column in {1, 3, 5} else 0)

        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value="Toutes les categories")
        self.status_var = tk.StringVar(value="Tous les statuts")

        ttk.Label(filters, text="Recherche").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.search_entry = ttk.Entry(filters, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(filters, text="Categorie").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.category_combo = ttk.Combobox(
            filters,
            textvariable=self.category_var,
            values=list(self.CATEGORY_OPTIONS.keys()),
            state="readonly",
        )
        self.category_combo.grid(row=0, column=3, sticky="ew", padx=(0, 12))
        ttk.Label(filters, text="Statut").grid(row=0, column=4, sticky="w", padx=(0, 8))
        self.status_combo = ttk.Combobox(
            filters,
            textvariable=self.status_var,
            values=list(self.STATUS_OPTIONS.keys()),
            state="readonly",
        )
        self.status_combo.grid(row=0, column=5, sticky="ew")
        ttk.Button(filters, text="Appliquer les filtres", command=self.refresh_data).grid(row=1, column=4, sticky="e", pady=(12, 0))
        ttk.Button(filters, text="Rafraichir l'USB", style="Accent.TButton", command=self._refresh_monitor).grid(
            row=1,
            column=5,
            sticky="e",
            pady=(12, 0),
        )
        self.search_var.trace_add("write", lambda *_args: self.schedule_refresh(250))
        self.search_entry.bind("<Return>", lambda _event: self.refresh_data())
        self.category_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_data())
        self.status_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_data())

        tree_frame = ttk.LabelFrame(self, text="Inventaire des peripheriques", style="Section.TLabelframe", padding=12)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        detail_frame = ttk.LabelFrame(self, text="Fiche peripherique", style="Section.TLabelframe", padding=12)
        detail_frame.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(3, weight=1)

        self.table = ScrollableTree(tree_frame, ("vidpid", "name", "category", "trust", "status", "score"), height=18)
        self.table.grid(row=0, column=0, sticky="nsew")
        for column, label, width in (
            ("vidpid", "VID:PID", 100),
            ("name", "Peripherique", 280),
            ("category", "Categorie", 120),
            ("trust", "Habitude", 115),
            ("status", "Etat", 105),
            ("score", "Score", 70),
        ):
            self.table.tree.heading(column, text=label)
            self.table.tree.column(column, width=width, anchor="w")
        self.table.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_selected())
        for tone in ("LOW", "MEDIUM", "HIGH", "CRITICAL", "connected", "disconnected", "KNOWN", "NEW", "RARE", "DEVIATION"):
            self.table.tree.tag_configure(tone, foreground=severity_color(tone))

        detail_top = ttk.Frame(detail_frame, style="Card.TFrame", padding=12)
        detail_top.grid(row=0, column=0, sticky="ew")
        detail_top.columnconfigure(0, weight=1)
        ttk.Label(detail_top, text="Selection actuelle", style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
        badge_row = ttk.Frame(detail_top, style="CardInner.TFrame")
        badge_row.grid(row=0, column=1, sticky="e")
        self.status_badge = StatusPill(badge_row, "INCONNU", "INFO")
        self.status_badge.pack(side="left")
        self.trust_badge = StatusPill(badge_row, "N/A", "INFO")
        self.trust_badge.pack(side="left", padx=(8, 0))
        self.risk_badge = StatusPill(badge_row, "LOW", "LOW")
        self.risk_badge.pack(side="left", padx=(8, 0))

        metrics = ttk.Frame(detail_frame, style="Card.TFrame", padding=12)
        metrics.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        for column in range(2):
            metrics.columnconfigure(column, weight=1)
        self.values = {
            "name": LabeledValue(metrics, "Nom"),
            "vidpid": LabeledValue(metrics, "VID:PID"),
            "serial": LabeledValue(metrics, "Numero de serie"),
            "category": LabeledValue(metrics, "Categorie"),
            "confidence": LabeledValue(metrics, "Confiance"),
            "backend": LabeledValue(metrics, "Backend"),
            "status": LabeledValue(metrics, "Etat"),
            "bus": LabeledValue(metrics, "Bus / Adresse"),
            "trust": LabeledValue(metrics, "Habitude"),
            "seen": LabeledValue(metrics, "Occurrences"),
            "decision": LabeledValue(metrics, "Derniere decision"),
            "variation": LabeledValue(metrics, "Variation"),
        }
        positions = [
            ("name", 0, 0),
            ("vidpid", 0, 1),
            ("serial", 1, 0),
            ("category", 1, 1),
            ("confidence", 2, 0),
            ("backend", 2, 1),
            ("status", 3, 0),
            ("bus", 3, 1),
            ("trust", 4, 0),
            ("seen", 4, 1),
            ("decision", 5, 0),
            ("variation", 5, 1),
        ]
        for key, row, column in positions:
            self.values[key].grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0), pady=6)

        actions = ttk.Frame(detail_frame)
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.whitelist_button = ttk.Button(
            actions,
            text="Ajouter a la liste blanche",
            style="Accent.TButton",
            command=self._whitelist,
            state="disabled",
        )
        self.whitelist_button.pack(side="left")
        self.blacklist_button = ttk.Button(
            actions,
            text="Ajouter a la liste noire",
            style="Danger.TButton",
            command=self._blacklist,
            state="disabled",
        )
        self.blacklist_button.pack(side="left", padx=8)

        self.detail_text = ScrollableDetailText(detail_frame, height=16)
        self.detail_text.grid(row=3, column=0, sticky="nsew")
        self._clear_selection_state()

    def refresh_data(self) -> None:
        selected_key = self._get_selected_device_key() or self._selected_device_key
        devices = self.controller.list_devices(
            search=self.search_var.get().strip(),
            category=self.CATEGORY_OPTIONS[self.category_var.get()],
            status=self.STATUS_OPTIONS[self.status_var.get()],
        )
        self._rows.clear()
        self.table.clear()
        item_to_restore: str | None = None
        for device in devices:
            item_id = self.table.tree.insert(
                "",
                "end",
                values=(
                    device.vid_pid,
                    shorten_text(device.display_name, 42),
                    category_text(device.category),
                    trust_state_text(device.trust_state),
                    device_status_text(device.status),
                    device.risk_score,
                ),
                tags=(device.risk_level, device.status, device.trust_state),
            )
            self._rows[item_id] = device
            if device.device_key == selected_key:
                item_to_restore = item_id
        self.table.set_empty(bool(devices), "Aucun peripherique ne correspond aux filtres actifs.")
        if item_to_restore is not None:
            self.table.tree.selection_set(item_to_restore)
            self.table.tree.focus(item_to_restore)
            self.table.tree.see(item_to_restore)
            self._show_selected()
        else:
            self._clear_selection_state()

    def _selected_device(self):
        selection = self.table.tree.selection()
        if not selection:
            return None
        return self._rows.get(selection[0])

    def _show_selected(self) -> None:
        device = self._selected_device()
        if device is None:
            self._clear_selection_state()
            return
        self._selected_device_key = device.device_key
        self.status_badge.set(device_status_text(device.status), device.status)
        self.trust_badge.set(trust_state_text(device.trust_state).upper(), trust_state_tone(device.trust_state))
        self.risk_badge.set(device.risk_level, device.risk_level)
        self.values["name"].set(device.display_name)
        self.values["vidpid"].set(device.vid_pid)
        self.values["serial"].set(device.serial_number or "Non disponible")
        self.values["category"].set(category_text(device.category))
        self.values["confidence"].set(f"{device.confidence:.0%}")
        self.values["backend"].set(device.source_backend)
        self.values["status"].set(device_status_text(device.status))
        self.values["bus"].set(f"{device.bus or '-'} / {device.address or '-'}")
        self.values["trust"].set(trust_state_text(device.trust_state))
        self.values["seen"].set(str(device.seen_count))
        self.values["decision"].set(decision_text(device.last_decision))
        self.values["variation"].set(device.recent_variation or "stable")
        history = (
            self.controller.get_device_history(device.device_key, limit=8)
            if hasattr(self.controller, "get_device_history")
            else []
        )
        history_lines = [
            f"- {format_for_ui(event.occurred_at)} | {event.event_type} | {event.severity} | {event.summary}"
            for event in history
        ] or ["- Aucun historique recent disponible."]
        self.detail_text.set_text(
            "Premiere observation : {first_seen}\n"
            "Derniere observation : {last_seen}\n"
            "Classe USB : {usb_class}\n"
            "Source d'identification : {source}\n"
            "Score de risque : {score}\n"
            "Plages d'usage : {usual_hours}\n"
            "Metadata : {metadata}\n\n"
            "Historique recent :\n{history}".format(
                first_seen=format_for_ui(device.first_seen),
                last_seen=format_for_ui(device.last_seen),
                usb_class=device.usb_class if device.usb_class is not None else "-",
                source=device.identification_source,
                score=f"{device.risk_level} ({device.risk_score})",
                usual_hours=device.usual_hours or {},
                metadata=device.metadata,
                history="\n".join(history_lines),
            )
        )
        self.whitelist_button.configure(state="normal")
        self.blacklist_button.configure(state="normal")

    def _clear_selection_state(self) -> None:
        self._selected_device_key = None
        self.status_badge.set("AUCUNE SELECTION", "INFO")
        self.trust_badge.set("N/A", "INFO")
        self.risk_badge.set("N/A", "INFO")
        for value in self.values.values():
            value.set("-")
        self.detail_text.set_text("Selectionnez un peripherique pour afficher sa fiche technique, sa baseline et son historique.")
        self.whitelist_button.configure(state="disabled")
        self.blacklist_button.configure(state="disabled")

    def _get_selected_device_key(self) -> str | None:
        device = self._selected_device()
        if device is None:
            return None
        return device.device_key

    def _whitelist(self) -> None:
        device = self._selected_device()
        if device is None:
            self.app.set_status("Selectionnez un peripherique a autoriser.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.whitelist_device(device.device_key),
            success_message="Peripherique ajoute a la liste blanche.",
        )

    def _blacklist(self) -> None:
        device = self._selected_device()
        if device is None:
            self.app.set_status("Selectionnez un peripherique a bloquer.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.blacklist_device(device.device_key),
            success_message="Peripherique ajoute a la liste noire.",
            success_level="HIGH",
        )

    def _refresh_monitor(self) -> None:
        self.controller.refresh_monitor()
        self.app.set_status("Rafraichissement USB demande.", "INFO")
