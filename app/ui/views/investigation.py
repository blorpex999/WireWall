from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk

from app.ui.controller import AppController
from app.ui.theme import COLORS, apply_dark_theme
from app.ui.widgets.common import LabeledValue, ScrollablePage, StatusPill
from app.ui.widgets.risk_breakdown import RiskBreakdownWidget
from app.utils.datetime import parse_timestamp
from app.utils.ui import category_text, decision_text, severity_color, shorten_text, trust_state_text, trust_state_tone

LOGGER = logging.getLogger(__name__)


class InvestigationWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, controller: AppController, device_key: str) -> None:
        super().__init__(parent)
        self.controller = controller
        self.device_key = device_key

        self.title(f"WireWall - Enquete : {device_key}")
        self.geometry("920x680")
        self.minsize(720, 500)
        self.configure(bg=COLORS["bg"])
        apply_dark_theme(self)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.page = ScrollablePage(self)
        self.page.grid(row=0, column=0, sticky="nsew")
        self.page.body.columnconfigure(0, weight=1)

        device = self.controller.get_device(device_key)
        if device is None:
            LOGGER.warning("Ouverture d'enquete impossible, device introuvable: %s", device_key)
            missing = ttk.LabelFrame(self.page.body, text="Peripherique", style="Section.TLabelframe", padding=16)
            missing.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
            ttk.Label(missing, text="Peripherique introuvable en base.", style="Muted.TLabel").grid(
                row=0,
                column=0,
                sticky="w",
            )
            ttk.Button(self.page.body, text="Fermer", style="Subtle.TButton", command=self.destroy).grid(
                row=1,
                column=0,
                sticky="e",
                padx=18,
                pady=(0, 18),
            )
            return

        identity = ttk.LabelFrame(self.page.body, text="Peripherique", style="Section.TLabelframe", padding=12)
        identity.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        identity.columnconfigure((0, 1, 2, 3), weight=1)

        LabeledValue(identity, "VID:PID", device.vid_pid).grid(row=0, column=0, sticky="ew", padx=(0, 12), pady=6)
        LabeledValue(identity, "Fabricant", device.vendor_name or "-").grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=6)
        LabeledValue(identity, "Produit", device.product_name or "-").grid(row=0, column=2, sticky="ew", padx=(0, 12), pady=6)
        LabeledValue(identity, "Numero de serie", device.serial_number or "-").grid(row=0, column=3, sticky="ew", pady=6)
        LabeledValue(identity, "Categorie", category_text(device.category)).grid(row=1, column=0, sticky="ew", padx=(0, 12), pady=6)
        trust_cell = tk.Frame(identity, bg=COLORS["panel"], bd=0, highlightthickness=0)
        trust_cell.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=6)
        trust_cell.columnconfigure(0, weight=1)
        self.trust_value = LabeledValue(trust_cell, "Trust state", trust_state_text(device.trust_state))
        self.trust_value.grid(row=0, column=0, sticky="ew")
        self.trust_badge = StatusPill(trust_cell, trust_state_text(device.trust_state).upper(), trust_state_tone(device.trust_state))
        self.trust_badge.grid(row=0, column=1, sticky="e", padx=(10, 0))
        LabeledValue(identity, "Seen count", str(device.seen_count)).grid(row=1, column=2, sticky="ew", padx=(0, 12), pady=6)
        LabeledValue(identity, "Derniere decision", decision_text(device.last_decision)).grid(row=1, column=3, sticky="ew", pady=6)

        timeline = ttk.LabelFrame(self.page.body, text="Timeline des evenements", style="Section.TLabelframe", padding=12)
        timeline.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        timeline.columnconfigure(0, weight=1)
        timeline.rowconfigure(0, weight=1)

        timeline_host = tk.Frame(timeline, bg=COLORS["panel"], bd=0, highlightthickness=0)
        timeline_host.grid(row=0, column=0, sticky="nsew")
        timeline_host.columnconfigure(0, weight=1)
        timeline_host.rowconfigure(0, weight=1)

        self.timeline_canvas = tk.Canvas(
            timeline_host,
            bg=COLORS["panel"],
            highlightthickness=0,
            bd=0,
            relief="flat",
            height=320,
        )
        self.timeline_canvas.grid(row=0, column=0, sticky="nsew")
        timeline_scroll = ttk.Scrollbar(timeline_host, orient="vertical", command=self.timeline_canvas.yview)
        timeline_scroll.grid(row=0, column=1, sticky="ns")
        self.timeline_canvas.configure(yscrollcommand=timeline_scroll.set)

        self.timeline_body = tk.Frame(self.timeline_canvas, bg=COLORS["panel"], bd=0, highlightthickness=0)
        self._timeline_window = self.timeline_canvas.create_window((0, 0), window=self.timeline_body, anchor="nw")
        self.timeline_body.bind("<Configure>", self._on_timeline_body_configure)
        self.timeline_canvas.bind("<Configure>", self._on_timeline_canvas_configure)
        self._render_timeline()

        assessment_frame = ttk.LabelFrame(self.page.body, text="Analyse de risque", style="Section.TLabelframe", padding=12)
        assessment_frame.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 12))
        assessment_frame.columnconfigure(0, weight=1)
        risk_widget = RiskBreakdownWidget(assessment_frame, surface="panel")
        risk_widget.grid(row=0, column=0, sticky="ew")
        risk_widget.update(self.controller.container.assessment_repo.latest(device_key))

        footer = ttk.Frame(self.page.body)
        footer.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))
        footer.columnconfigure(0, weight=1)
        ttk.Button(footer, text="Fermer", style="Subtle.TButton", command=self.destroy).grid(row=0, column=1, sticky="e")

    def _render_timeline(self) -> None:
        for child in self.timeline_body.winfo_children():
            child.destroy()

        events = sorted(
            self.controller.get_device_history(self.device_key, limit=100),
            key=lambda event: event.occurred_at,
            reverse=True,
        )
        if not events:
            tk.Label(
                self.timeline_body,
                text="Aucun evenement enregistre pour ce peripherique.",
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                font=("Segoe UI", 10),
                anchor="w",
            ).grid(row=0, column=0, sticky="ew", padx=12, pady=12)
            return

        self.timeline_body.columnconfigure(0, weight=1)
        for index, event in enumerate(events):
            row_bg = COLORS["panel"] if index % 2 == 0 else COLORS["panel_alt"]
            row = tk.Frame(self.timeline_body, bg=row_bg, bd=0, highlightthickness=0, padx=12, pady=10)
            row.grid(row=index, column=0, sticky="ew")
            row.columnconfigure(3, weight=1)

            tk.Label(
                row,
                text=self._timeline_time(event.occurred_at),
                bg=row_bg,
                fg=COLORS["muted"],
                font=("Consolas", 10),
            ).grid(row=0, column=0, sticky="w", padx=(0, 10))
            tk.Label(
                row,
                text="\u25CF",
                bg=row_bg,
                fg=severity_color(event.severity),
                padx=4,
                font=("Segoe UI", 11),
            ).grid(row=0, column=1, sticky="w", padx=(0, 10))
            tk.Label(
                row,
                text=event.event_type,
                bg=row_bg,
                fg=COLORS["text"],
                font=("Segoe UI Semibold", 10),
            ).grid(row=0, column=2, sticky="w", padx=(0, 10))
            tk.Label(
                row,
                text=shorten_text(event.summary, 80),
                bg=row_bg,
                fg=COLORS["text"],
                font=("Segoe UI", 10),
                anchor="w",
                justify="left",
            ).grid(row=0, column=3, sticky="ew", padx=(0, 10))
            StatusPill(row, event.severity, event.severity).grid(row=0, column=4, sticky="e")

    def _on_timeline_body_configure(self, _event: tk.Event) -> None:
        self.timeline_canvas.configure(scrollregion=self.timeline_canvas.bbox("all"))

    def _on_timeline_canvas_configure(self, event: tk.Event) -> None:
        self.timeline_canvas.itemconfigure(self._timeline_window, width=event.width)

    def _timeline_time(self, value: str | None) -> str:
        parsed = parse_timestamp(value)
        if parsed is None:
            return "--:--:--  --/--"
        return parsed.astimezone().strftime("%H:%M:%S  %d/%m")
