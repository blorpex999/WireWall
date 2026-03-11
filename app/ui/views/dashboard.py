from __future__ import annotations

from tkinter import ttk

from app.ui.views.base import BaseView
from app.ui.widgets.common import KpiCard, LabeledValue, ScrollableTree, SectionHeader, StatusPill
from app.utils.datetime import format_for_ui
from app.utils.ui import device_status_text, health_status_text, risk_level_from_score, severity_color, shorten_text, tone_for_status


class DashboardView(BaseView):
    view_title = "Tableau de bord"

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        for column in range(4):
            self.columnconfigure(column, weight=1)
        self.rowconfigure(3, weight=2)
        self.rowconfigure(4, weight=1)

        self.header = SectionHeader(
            self,
            "Tableau de bord",
            "Vue de synthese de l'activite USB, des alertes et de l'etat de la plateforme.",
            "MODE DEMO" if self.controller.demo_mode else "MODE REEL",
            "WARNING" if self.controller.demo_mode else "INFO",
        )
        self.header.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 16))

        strip = ttk.Frame(self, style="Card.TFrame", padding=16)
        strip.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 12))
        for column in range(4):
            strip.columnconfigure(column, weight=1)
        self.usb_tile = self._build_tile(strip, 0, "Stockage USB")
        self.ollama_tile = self._build_tile(strip, 1, "Ollama local")
        self.health_tile = self._build_tile(strip, 2, "Sante plateforme")
        self.admin_tile = self._build_tile(strip, 3, "Session")

        self.card_score = KpiCard(self, "Risque global")
        self.card_devices = KpiCard(self, "Peripheriques actifs")
        self.card_events = KpiCard(self, "Evenements 24h")
        self.card_alerts = KpiCard(self, "Alertes critiques")
        self.card_score.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        self.card_devices.grid(row=2, column=1, sticky="nsew", padx=8, pady=(0, 12))
        self.card_events.grid(row=2, column=2, sticky="nsew", padx=8, pady=(0, 12))
        self.card_alerts.grid(row=2, column=3, sticky="nsew", padx=(8, 0), pady=(0, 12))

        events_frame = ttk.LabelFrame(self, text="Activite recente", style="Section.TLabelframe", padding=12)
        events_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=(0, 8), pady=(0, 12))
        alerts_frame = ttk.LabelFrame(self, text="Alertes prioritaires", style="Section.TLabelframe", padding=12)
        alerts_frame.grid(row=3, column=2, columnspan=2, sticky="nsew", padx=(8, 0), pady=(0, 12))
        health_frame = ttk.LabelFrame(self, text="Etat des composants", style="Section.TLabelframe", padding=12)
        health_frame.grid(row=4, column=0, columnspan=4, sticky="nsew")

        self.event_table = ScrollableTree(events_frame, ("date", "type", "summary", "severity"), height=9)
        self.event_table.pack(fill="both", expand=True)
        for column, label, width in (
            ("date", "Date", 145),
            ("type", "Type", 120),
            ("summary", "Resume", 420),
            ("severity", "Gravite", 100),
        ):
            self.event_table.tree.heading(column, text=label)
            self.event_table.tree.column(column, width=width, anchor="w")

        self.alert_table = ScrollableTree(alerts_frame, ("date", "severity", "title", "score"), height=9)
        self.alert_table.pack(fill="both", expand=True)
        for column, label, width in (
            ("date", "Date", 145),
            ("severity", "Gravite", 95),
            ("title", "Titre", 330),
            ("score", "Score", 70),
        ):
            self.alert_table.tree.heading(column, text=label)
            self.alert_table.tree.column(column, width=width, anchor="w")

        self.health_table = ScrollableTree(health_frame, ("component", "status", "details"), height=6)
        self.health_table.pack(fill="both", expand=True)
        for column, label, width in (
            ("component", "Composant", 180),
            ("status", "Etat", 130),
            ("details", "Detail", 900),
        ):
            self.health_table.tree.heading(column, text=label)
            self.health_table.tree.column(column, width=width, anchor="w")

        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL", "INFO", "WARNING", "ERROR", "OK"):
            self.event_table.tree.tag_configure(level, foreground=severity_color(level))
            self.alert_table.tree.tag_configure(level, foreground=severity_color(level))
            self.health_table.tree.tag_configure(level, foreground=severity_color(level))

    def refresh_data(self) -> None:
        data = self.controller.get_dashboard_data()
        risk_level = risk_level_from_score(data["global_score"])
        self.card_score.set(str(data["global_score"]), f"Niveau {risk_level}", tone=risk_level, pill_text=risk_level)
        self.card_devices.set(str(data["connected_count"]), f"{data['device_count']} inventorie(s)", tone="INFO", pill_text="ACTIFS")
        self.card_events.set(str(data["events_today"]), "Trace audit sur 24 heures", tone="INFO", pill_text="AUDIT")
        alert_tone = "CRITICAL" if data["critical_alerts"] else "OK"
        self.card_alerts.set(
            str(data["critical_alerts"]),
            f"{data['alerts_total']} alerte(s) au total",
            tone=alert_tone,
            pill_text="CRITIQUE" if data["critical_alerts"] else "CALME",
        )

        health_map = {status.component: status for status in data["health"]}
        admin_status = health_map.get("admin")
        ollama_status = data["ollama_status"]
        usb_status = data["usb_status"]

        self._set_tile(self.usb_tile, device_status_text(usb_status.status), shorten_text(usb_status.message, 56), tone_for_status(usb_status.status))
        self._set_tile(
            self.ollama_tile,
            health_status_text(ollama_status.status),
            shorten_text(ollama_status.details, 56),
            tone_for_status(ollama_status.status),
        )
        ok_count = sum(1 for item in data["health"] if item.status == "ok")
        health_tone = "OK" if ok_count == len(data["health"]) and data["health"] else "WARNING"
        self._set_tile(self.health_tile, f"{ok_count}/{len(data['health']) or 0}", "Composants OK", health_tone)
        session_value = "Admin" if admin_status and admin_status.status == "ok" else "Standard"
        self._set_tile(
            self.admin_tile,
            session_value,
            shorten_text(admin_status.details if admin_status else "Statut inconnu.", 56),
            tone_for_status(admin_status.status if admin_status else "warning"),
        )

        self.event_table.clear()
        self.alert_table.clear()
        self.health_table.clear()

        for event in data["recent_events"]:
            self.event_table.tree.insert(
                "",
                "end",
                values=(format_for_ui(event.occurred_at), event.event_type, shorten_text(event.summary, 84), event.severity),
                tags=(event.severity,),
            )
        self.event_table.set_empty(bool(data["recent_events"]), "Aucun evenement recent a afficher.")

        for alert in data["top_alerts"]:
            self.alert_table.tree.insert(
                "",
                "end",
                values=(format_for_ui(alert.created_at), alert.severity, shorten_text(alert.title, 64), alert.score),
                tags=(alert.severity,),
            )
        self.alert_table.set_empty(bool(data["top_alerts"]), "Aucune alerte critique recente.")

        for status in data["health"]:
            self.health_table.tree.insert(
                "",
                "end",
                values=(status.component, health_status_text(status.status), shorten_text(status.details, 120)),
                tags=(tone_for_status(status.status),),
            )
        self.health_table.set_empty(bool(data["health"]), "Aucun health check disponible pour le moment.")

    def _build_tile(self, master, column: int, title: str) -> dict[str, object]:
        frame = ttk.Frame(master, style="CardInner.TFrame", padding=(8, 4))
        frame.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=title, style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
        pill = StatusPill(frame, "", "INFO")
        pill.grid(row=0, column=1, sticky="e")
        value = LabeledValue(frame, "Etat", "-")
        value.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        detail = ttk.Label(frame, text="", style="Muted.TLabel", wraplength=250, justify="left")
        detail.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        return {"value": value, "detail": detail, "pill": pill}

    def _set_tile(self, tile: dict[str, object], value: str, detail: str, tone: str) -> None:
        tile["value"].set(value)
        tile["detail"].configure(text=detail)
        tile["pill"].set(tone.upper(), tone)
