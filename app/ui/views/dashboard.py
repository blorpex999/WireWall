from __future__ import annotations

from tkinter import ttk

from app.ui.views.base import BaseView
from app.ui.help_content import SCREEN_HELP
from app.ui.widgets.common import InlineHelpPanel, KpiCard, LabeledValue, ScrollableTree, SectionHeader, StatusPill
from app.utils.datetime import format_for_ui
from app.utils.ui import (
    decision_text,
    device_status_text,
    health_status_text,
    recommendation_priority_text,
    risk_level_from_score,
    severity_color,
    shorten_text,
    tone_for_status,
)


class DashboardView(BaseView):
    view_title = "Tableau de bord"

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        for column in range(5):
            self.columnconfigure(column, weight=1)
        self.rowconfigure(4, weight=2)
        self.rowconfigure(5, weight=1)
        self.rowconfigure(6, weight=1)
        self.rowconfigure(7, weight=0)
        self.rowconfigure(8, weight=0)
        self._suggestion_rows: dict[str, object] = {}
        self._dashboard_mode = ""
        self._dashboard_width = 1450
        self._section_wrap_labels: list[ttk.Label] = []

        self.header = SectionHeader(
            self,
            "Tableau de bord",
            "Vue de synthese de l'activite USB, des incidents, des suggestions et de l'etat de la plateforme.",
            "MODE DEMO" if self.controller.demo_mode else "MODE REEL",
            "WARNING" if self.controller.demo_mode else "INFO",
        )
        self.header.grid(row=0, column=0, columnspan=5, sticky="ew", pady=(0, 16))

        self.help_panel = InlineHelpPanel(
            self,
            button_text=str(SCREEN_HELP["dashboard"]["button"]),
            sections=list(SCREEN_HELP["dashboard"]["sections"]),
        )
        self.help_panel.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(0, 12))

        self.status_strip = ttk.Frame(self, style="Card.TFrame", padding=16)
        self.status_strip.grid(row=2, column=0, columnspan=5, sticky="ew", pady=(0, 12))
        self.usb_tile = self._build_tile(self.status_strip, "Stockage USB")
        self.ollama_tile = self._build_tile(self.status_strip, "Ollama local")
        self.health_tile = self._build_tile(self.status_strip, "Sante plateforme")
        self.admin_tile = self._build_tile(self.status_strip, "Session")
        self._status_tiles = [self.usb_tile, self.ollama_tile, self.health_tile, self.admin_tile]

        self.kpi_frame = ttk.Frame(self)
        self.kpi_frame.grid(row=3, column=0, columnspan=5, sticky="nsew", pady=(0, 12))
        self.card_score = KpiCard(self.kpi_frame, "Risque global")
        self.card_devices = KpiCard(self.kpi_frame, "Peripheriques actifs")
        self.card_incidents = KpiCard(self.kpi_frame, "Incidents ouverts")
        self.card_alerts = KpiCard(self.kpi_frame, "Alertes critiques")
        self.card_suggestions = KpiCard(self.kpi_frame, "Suggestions")
        self._kpi_cards = [
            self.card_score,
            self.card_devices,
            self.card_incidents,
            self.card_alerts,
            self.card_suggestions,
        ]

        self.upper_frame = ttk.Frame(self)
        self.upper_frame.grid(row=4, column=0, columnspan=5, sticky="nsew", pady=(0, 12))
        self.upper_frame.columnconfigure(0, weight=1)
        self.upper_frame.columnconfigure(1, weight=1)
        self.upper_frame.rowconfigure(0, weight=1)
        self.upper_frame.rowconfigure(1, weight=1)
        events_frame = ttk.LabelFrame(self.upper_frame, text="Activite recente", style="Section.TLabelframe", padding=12)
        alerts_frame = ttk.LabelFrame(self.upper_frame, text="Alertes prioritaires", style="Section.TLabelframe", padding=12)

        self.middle_frame = ttk.Frame(self)
        self.middle_frame.grid(row=5, column=0, columnspan=5, sticky="nsew")
        self.middle_frame.columnconfigure(0, weight=1)
        self.middle_frame.columnconfigure(1, weight=1)
        self.middle_frame.rowconfigure(0, weight=1)
        self.middle_frame.rowconfigure(1, weight=1)
        health_frame = ttk.LabelFrame(self.middle_frame, text="Etat des composants", style="Section.TLabelframe", padding=12)
        brain_frame = ttk.LabelFrame(self.middle_frame, text="Moteur d'analyse continu", style="Section.TLabelframe", padding=12)

        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.grid(row=6, column=0, columnspan=5, sticky="nsew", pady=(12, 0))
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(1, weight=1)
        self.bottom_frame.rowconfigure(0, weight=1)
        self.bottom_frame.rowconfigure(1, weight=1)
        suggestions_frame = ttk.LabelFrame(self.bottom_frame, text="Suggestions supervisees", style="Section.TLabelframe", padding=12)
        precheck_frame = ttk.LabelFrame(self.bottom_frame, text="Precheck demo", style="Section.TLabelframe", padding=12)

        self._section_frames = {
            "events": events_frame,
            "alerts": alerts_frame,
            "health": health_frame,
            "brain": brain_frame,
            "suggestions": suggestions_frame,
            "precheck": precheck_frame,
        }
        brain_frame.columnconfigure(0, weight=1)
        brain_frame.columnconfigure(1, weight=1)
        brain_frame.columnconfigure(2, weight=1)
        suggestions_frame.columnconfigure(0, weight=1)
        suggestions_frame.rowconfigure(1, weight=1)
        precheck_frame.columnconfigure(0, weight=1)
        precheck_frame.rowconfigure(1, weight=1)

        self.event_table = ScrollableTree(events_frame, ("date", "type", "summary", "severity"), height=6)
        self.event_table.pack(fill="both", expand=True)
        for column, label, width in (
            ("date", "Date", 145),
            ("type", "Type", 120),
            ("summary", "Resume", 420),
            ("severity", "Gravite", 100),
        ):
            self.event_table.tree.heading(column, text=label)
            self.event_table.tree.column(column, width=width, anchor="w")

        self.alert_table = ScrollableTree(alerts_frame, ("date", "severity", "title", "score"), height=6)
        self.alert_table.pack(fill="both", expand=True)
        for column, label, width in (
            ("date", "Date", 145),
            ("severity", "Gravite", 95),
            ("title", "Titre", 330),
            ("score", "Score", 70),
        ):
            self.alert_table.tree.heading(column, text=label)
            self.alert_table.tree.column(column, width=width, anchor="w")

        self.health_table = ScrollableTree(health_frame, ("component", "status", "details"), height=4)
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

        self.brain_level_badge = StatusPill(brain_frame, "N/A", "INFO")
        self.brain_level_badge.grid(row=0, column=1, sticky="e", padx=(12, 8))
        self.brain_progress_badge = StatusPill(brain_frame, "STABLE", "INFO")
        self.brain_progress_badge.grid(row=0, column=2, sticky="e")
        self.brain_summary = ttk.Label(brain_frame, text="", style="Muted.TLabel", wraplength=600, justify="left")
        self.brain_summary.grid(row=0, column=0, sticky="w")
        self.brain_incidents = LabeledValue(brain_frame, "Incidents actifs", "-")
        self.brain_incidents.grid(row=1, column=0, sticky="ew", pady=(12, 0), padx=(0, 12))
        self.brain_alerts = LabeledValue(brain_frame, "Alertes ouvertes", "-")
        self.brain_alerts.grid(row=1, column=1, sticky="ew", pady=(12, 0), padx=(0, 12))
        self.brain_focus = LabeledValue(brain_frame, "Points de focus", "-")
        self.brain_focus.grid(row=1, column=2, sticky="ew", pady=(12, 0))
        self.brain_new_devices = LabeledValue(brain_frame, "Nouveaux 7 jours", "-")
        self.brain_new_devices.grid(row=2, column=0, sticky="ew", pady=(12, 0), padx=(0, 12))
        self.brain_deviations = LabeledValue(brain_frame, "Deviations actives", "-")
        self.brain_deviations.grid(row=2, column=1, sticky="ew", pady=(12, 0), padx=(0, 12))
        self.brain_known = LabeledValue(brain_frame, "Parc habituel", "-")
        self.brain_known.grid(row=2, column=2, sticky="ew", pady=(12, 0))

        self.suggestion_table = ScrollableTree(suggestions_frame, ("priority", "title", "action", "device"), height=4)
        self.suggestion_table.grid(row=1, column=0, sticky="nsew")
        for column, label, width in (
            ("priority", "Priorite", 110),
            ("title", "Titre", 360),
            ("action", "Action proposee", 220),
            ("device", "Peripherique", 240),
        ):
            self.suggestion_table.tree.heading(column, text=label)
            self.suggestion_table.tree.column(column, width=width, anchor="w")
        self.suggestion_table.tree.bind("<<TreeviewSelect>>", lambda _event: self._sync_suggestion_actions())
        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            self.suggestion_table.tree.tag_configure(level, foreground=severity_color(level))

        suggestion_actions = ttk.Frame(suggestions_frame)
        suggestion_actions.grid(row=0, column=0, sticky="e", pady=(0, 10))
        self.accept_button = ttk.Button(
            suggestion_actions,
            text="Accepter",
            style="Accent.TButton",
            command=self._accept_suggestion,
            state="disabled",
        )
        self.accept_button.pack(side="left")
        self.defer_button = ttk.Button(
            suggestion_actions,
            text="Reporter",
            style="Subtle.TButton",
            command=self._defer_suggestion,
            state="disabled",
        )
        self.defer_button.pack(side="left", padx=8)
        self.reject_button = ttk.Button(
            suggestion_actions,
            text="Refuser",
            style="Danger.TButton",
            command=self._reject_suggestion,
            state="disabled",
        )
        self.reject_button.pack(side="left")

        self.precheck_intro = ttk.Label(
            precheck_frame,
            text="Lecture seule. Aucun effet de bord. Utilise les checks existants pour preparer la demo.",
            style="Muted.TLabel",
            wraplength=520,
            justify="left",
        )
        self.precheck_intro.grid(row=0, column=0, sticky="w", pady=(0, 10))
        self._section_wrap_labels.extend([self.brain_summary, self.precheck_intro])
        self.precheck_table = ScrollableTree(precheck_frame, ("item", "status", "action"), height=4)
        self.precheck_table.grid(row=1, column=0, sticky="nsew")
        for column, label, width in (
            ("item", "Point", 170),
            ("status", "Etat", 110),
            ("action", "Action conseillee", 340),
        ):
            self.precheck_table.tree.heading(column, text=label)
            self.precheck_table.tree.column(column, width=width, anchor="w")
        for tone in ("OK", "WARNING", "ERROR"):
            self.precheck_table.tree.tag_configure(tone, foreground=severity_color(tone))

        self._apply_layout("wide")
        self._update_wrap_lengths()

    def refresh_data(self) -> None:
        data = self.controller.get_dashboard_data()
        risk_level = risk_level_from_score(data["global_score"])
        self.card_score.set(str(data["global_score"]), f"Niveau {risk_level}", tone=risk_level, pill_text=risk_level)
        self.card_devices.set(str(data["connected_count"]), f"{data['device_count']} inventorie(s)", tone="INFO", pill_text="ACTIFS")
        self.card_incidents.set(
            str(data["open_incidents"]),
            f"{data['deviation_count']} deviation(s) active(s)",
            tone="HIGH" if data["open_incidents"] else "OK",
            pill_text="INCIDENTS",
        )
        alert_tone = "CRITICAL" if data["critical_alerts"] else "OK"
        self.card_alerts.set(
            str(data["critical_alerts"]),
            f"{data['alerts_total']} alerte(s) au total",
            tone=alert_tone,
            pill_text="CRITIQUE" if data["critical_alerts"] else "CALME",
        )
        suggestion_tone = "HIGH" if data["suggestions"] else "INFO"
        self.card_suggestions.set(
            str(len(data["suggestions"])),
            f"{data['new_devices_7d']} nouveau(x) sur 7 jours",
            tone=suggestion_tone,
            pill_text="SUPERVISE",
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
        self.suggestion_table.clear()
        self.precheck_table.clear()
        self._suggestion_rows.clear()

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

        for suggestion in data["suggestions"]:
            item_id = self.suggestion_table.tree.insert(
                "",
                "end",
                values=(
                    recommendation_priority_text(suggestion.priority),
                    shorten_text(suggestion.title, 58),
                    decision_text(suggestion.proposed_action.replace("_device", "")),
                    shorten_text(suggestion.target_device_key or "-", 32),
                ),
                tags=(suggestion.priority,),
            )
            self._suggestion_rows[item_id] = suggestion
        self.suggestion_table.set_empty(bool(data["suggestions"]), "Aucune suggestion a valider pour le moment.")
        self._sync_suggestion_actions()

        precheck_rows = self.controller.get_demo_precheck()
        for row in precheck_rows:
            self.precheck_table.tree.insert(
                "",
                "end",
                values=(row["label"], row["status"], shorten_text(row["action"], 76)),
                tags=(row["tone"],),
            )
        self.precheck_table.set_empty(bool(precheck_rows), "Aucun precheck disponible.")

        brain_snapshot = data.get("brain_snapshot")
        if brain_snapshot is None:
            self.brain_level_badge.set("N/A", "INFO")
            self.brain_progress_badge.set("EN ATTENTE", "INFO")
            self.brain_summary.configure(text="Le moteur d'analyse n'a pas encore produit de synthese continue.")
            self.brain_incidents.set("-")
            self.brain_alerts.set("-")
            self.brain_focus.set("-")
            self.brain_new_devices.set("-")
            self.brain_deviations.set("-")
            self.brain_known.set("-")
            return

        progress_tone = {
            "LEARNING": "INFO",
            "STABLE": "OK",
            "IMPROVING": "OK",
            "DETERIORATING": "WARNING",
        }.get(brain_snapshot.progress_status, "INFO")
        self.brain_level_badge.set(brain_snapshot.global_level, brain_snapshot.global_level)
        self.brain_progress_badge.set(brain_snapshot.progress_status, progress_tone)
        self.brain_summary.configure(text=brain_snapshot.summary)
        self.brain_incidents.set(str(brain_snapshot.open_incident_count))
        self.brain_alerts.set(str(brain_snapshot.open_alert_count))
        self.brain_focus.set(", ".join(brain_snapshot.focus_areas) if brain_snapshot.focus_areas else "Aucun focus prioritaire")
        self.brain_new_devices.set(str(data["new_devices_7d"]))
        self.brain_deviations.set(str(brain_snapshot.deviation_count))
        self.brain_known.set(str(data["known_count"]))

    def on_host_resize(self, width: int, height: int) -> None:
        self._dashboard_width = max(width, 960)
        if width < 1080:
            mode = "compact"
        elif width < 1320:
            mode = "medium"
        else:
            mode = "wide"
        self._apply_layout(mode)
        self._update_wrap_lengths()

    def _build_tile(self, master, title: str) -> dict[str, object]:
        frame = ttk.Frame(master, style="CardInner.TFrame", padding=(8, 4))
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=title, style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
        pill = StatusPill(frame, "", "INFO")
        pill.grid(row=0, column=1, sticky="e")
        value = LabeledValue(frame, "Etat", "-")
        value.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        detail = ttk.Label(frame, text="", style="Muted.TLabel", wraplength=250, justify="left")
        detail.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._section_wrap_labels.append(detail)
        return {"frame": frame, "value": value, "detail": detail, "pill": pill}

    def _set_tile(self, tile: dict[str, object], value: str, detail: str, tone: str) -> None:
        tile["value"].set(value)
        tile["detail"].configure(text=detail)
        tile["pill"].set(tone.upper(), tone)

    def _apply_layout(self, mode: str) -> None:
        if mode == self._dashboard_mode:
            return
        self._dashboard_mode = mode

        for column in range(5):
            self.kpi_frame.columnconfigure(column, weight=0)
        for column in range(4):
            self.status_strip.columnconfigure(column, weight=0)
        for row in range(4):
            self.status_strip.rowconfigure(row, weight=0)
        for row in range(6):
            self.kpi_frame.rowconfigure(row, weight=0)
        for widget in self._kpi_cards:
            widget.grid_forget()
        for tile in self._status_tiles:
            tile["frame"].grid_forget()
        for frame in self._section_frames.values():
            frame.grid_forget()

        if mode == "compact":
            for column in range(2):
                self.status_strip.columnconfigure(column, weight=1)
            for index, tile in enumerate(self._status_tiles):
                row = index // 2
                column = index % 2
                tile["frame"].grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0), pady=(0, 8))
            for row in range(2):
                self.status_strip.rowconfigure(row, weight=1)

            for column in range(2):
                self.kpi_frame.columnconfigure(column, weight=1)
            for index, widget in enumerate(self._kpi_cards):
                row = index // 2
                column = index % 2
                if index == 4:
                    row = 2
                    column = 0
                    widget.grid(row=row, column=column, columnspan=2, sticky="nsew", padx=0, pady=(0, 12))
                    continue
                widget.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0), pady=(0, 12))
            for row in range(3):
                self.kpi_frame.rowconfigure(row, weight=1)

            self._section_frames["events"].grid(row=0, column=0, sticky="nsew", pady=(0, 12))
            self._section_frames["alerts"].grid(row=1, column=0, sticky="nsew", pady=(0, 12))
            self._section_frames["health"].grid(row=0, column=0, sticky="nsew", pady=(0, 12))
            self._section_frames["brain"].grid(row=1, column=0, sticky="nsew")
            self._section_frames["suggestions"].grid(row=0, column=0, sticky="nsew", pady=(0, 12))
            self._section_frames["precheck"].grid(row=1, column=0, sticky="nsew")
            self.upper_frame.columnconfigure(0, weight=1)
            self.upper_frame.columnconfigure(1, weight=0)
            self.middle_frame.columnconfigure(0, weight=1)
            self.middle_frame.columnconfigure(1, weight=0)
            self.bottom_frame.columnconfigure(0, weight=1)
            self.bottom_frame.columnconfigure(1, weight=0)
        elif mode == "medium":
            for column in range(2):
                self.status_strip.columnconfigure(column, weight=1)
            for index, tile in enumerate(self._status_tiles):
                row = index // 2
                column = index % 2
                tile["frame"].grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0), pady=(0, 8))
            for row in range(2):
                self.status_strip.rowconfigure(row, weight=1)

            for column in range(3):
                self.kpi_frame.columnconfigure(column, weight=1)
            for index, widget in enumerate(self._kpi_cards):
                row = index // 3
                column = index % 3
                widget.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0), pady=(0, 12))
            for row in range(2):
                self.kpi_frame.rowconfigure(row, weight=1)

            self._section_frames["events"].grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
            self._section_frames["alerts"].grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
            self._section_frames["health"].grid(row=0, column=0, sticky="nsew", padx=(0, 8))
            self._section_frames["brain"].grid(row=0, column=1, sticky="nsew", padx=(8, 0))
            self._section_frames["suggestions"].grid(row=0, column=0, sticky="nsew", pady=(0, 12))
            self._section_frames["precheck"].grid(row=1, column=0, columnspan=2, sticky="nsew")
            self.upper_frame.columnconfigure(0, weight=1)
            self.upper_frame.columnconfigure(1, weight=1)
            self.middle_frame.columnconfigure(0, weight=1)
            self.middle_frame.columnconfigure(1, weight=1)
            self.bottom_frame.columnconfigure(0, weight=1)
            self.bottom_frame.columnconfigure(1, weight=1)
        else:
            for column in range(4):
                self.status_strip.columnconfigure(column, weight=1)
            for index, tile in enumerate(self._status_tiles):
                tile["frame"].grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0))
            self.status_strip.rowconfigure(0, weight=1)

            for column in range(5):
                self.kpi_frame.columnconfigure(column, weight=1)
            for index, widget in enumerate(self._kpi_cards):
                widget.grid(
                    row=0,
                    column=index,
                    sticky="nsew",
                    padx=(0 if index == 0 else 8, 0),
                    pady=(0, 12),
                )
            self.kpi_frame.rowconfigure(0, weight=1)

            self._section_frames["events"].grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
            self._section_frames["alerts"].grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
            self._section_frames["health"].grid(row=0, column=0, sticky="nsew", padx=(0, 8))
            self._section_frames["brain"].grid(row=0, column=1, sticky="nsew", padx=(8, 0))
            self._section_frames["suggestions"].grid(row=0, column=0, sticky="nsew", padx=(0, 8))
            self._section_frames["precheck"].grid(row=0, column=1, sticky="nsew", padx=(8, 0))
            self.upper_frame.columnconfigure(0, weight=1)
            self.upper_frame.columnconfigure(1, weight=1)
            self.middle_frame.columnconfigure(0, weight=1)
            self.middle_frame.columnconfigure(1, weight=1)
            self.bottom_frame.columnconfigure(0, weight=1)
            self.bottom_frame.columnconfigure(1, weight=1)

        self._update_wrap_lengths()

    def _update_wrap_lengths(self) -> None:
        if not hasattr(self, "brain_summary") or not hasattr(self, "precheck_intro"):
            return
        if self._dashboard_mode == "compact":
            tile_wrap = 180
            summary_wrap = 360
            precheck_wrap = 420
            event_height = 4
            side_height = 3
        elif self._dashboard_mode == "medium":
            tile_wrap = 220
            summary_wrap = 420
            precheck_wrap = 520
            event_height = 5
            side_height = 4
        else:
            tile_wrap = 250
            summary_wrap = 620
            precheck_wrap = 560
            event_height = 6
            side_height = 4

        for tile in self._status_tiles:
            tile["detail"].configure(wraplength=tile_wrap)
        self.brain_summary.configure(wraplength=summary_wrap)
        self.precheck_intro.configure(wraplength=precheck_wrap)
        self.event_table.tree.configure(height=event_height)
        self.alert_table.tree.configure(height=event_height)
        self.health_table.tree.configure(height=side_height)
        self.suggestion_table.tree.configure(height=side_height)
        self.precheck_table.tree.configure(height=side_height)

    def _selected_suggestion(self):
        selection = self.suggestion_table.tree.selection()
        if not selection:
            return None
        return self._suggestion_rows.get(selection[0])

    def _sync_suggestion_actions(self) -> None:
        state = "normal" if self._selected_suggestion() is not None else "disabled"
        self.accept_button.configure(state=state)
        self.defer_button.configure(state=state)
        self.reject_button.configure(state=state)

    def _accept_suggestion(self) -> None:
        suggestion = self._selected_suggestion()
        if suggestion is None or suggestion.id is None:
            self.app.set_status("Selectionnez une suggestion a accepter.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.accept_suggestion(suggestion.id),
            success_message="Suggestion acceptee et appliquee.",
            refresh=True,
        )

    def _defer_suggestion(self) -> None:
        suggestion = self._selected_suggestion()
        if suggestion is None or suggestion.id is None:
            self.app.set_status("Selectionnez une suggestion a reporter.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.defer_suggestion(suggestion.id),
            success_message="Suggestion reportee.",
            refresh=True,
        )

    def _reject_suggestion(self) -> None:
        suggestion = self._selected_suggestion()
        if suggestion is None or suggestion.id is None:
            self.app.set_status("Selectionnez une suggestion a refuser.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.reject_suggestion(suggestion.id),
            success_message="Suggestion refusee.",
            refresh=True,
        )
