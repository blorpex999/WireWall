from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.help_content import SCREEN_HELP
from app.ui.theme import COLORS
from app.ui.views.base import BaseView
from app.ui.widgets.common import InlineHelpPanel, KpiCard, LabeledValue, ScrollablePage, ScrollableTree, SectionHeader, StatusPill
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

    def __init__(self, parent, controller, app) -> None:
        super().__init__(parent, controller, app)
        self._suggestion_rows: dict[str, object] = {}
        self._dashboard_mode = ""
        self._dashboard_width = 1450
        self._section_wrap_labels: list[QLabel] = []

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        self.page = ScrollablePage(self)
        root_layout.addWidget(self.page)

        self.content = QWidget(self.page.body)
        self.page.body_layout.addWidget(self.content)
        self.content_layout = QGridLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setHorizontalSpacing(0)
        self.content_layout.setVerticalSpacing(12)

        self.header = SectionHeader(
            self.content,
            "Tableau de bord",
            "Vue de synthese de l'activite USB, des incidents, des suggestions et de l'etat de la plateforme.",
            "MODE DEMO" if self.controller.demo_mode else "MODE REEL",
            "WARNING" if self.controller.demo_mode else "INFO",
        )
        self.content_layout.addWidget(self.header, 0, 0)

        self.help_panel = InlineHelpPanel(
            self.content,
            button_text=str(SCREEN_HELP["dashboard"]["button"]),
            sections=list(SCREEN_HELP["dashboard"]["sections"]),
        )
        self.content_layout.addWidget(self.help_panel, 1, 0)

        self.status_strip = QFrame(self.content)
        self.status_strip.setObjectName("card")
        self.status_layout = QGridLayout(self.status_strip)
        self.status_layout.setContentsMargins(16, 16, 16, 16)
        self.status_layout.setHorizontalSpacing(8)
        self.status_layout.setVerticalSpacing(8)
        self.content_layout.addWidget(self.status_strip, 2, 0)
        self.usb_tile = self._build_tile(self.status_strip, "Stockage USB")
        self.ollama_tile = self._build_tile(self.status_strip, "Ollama local")
        self.health_tile = self._build_tile(self.status_strip, "Sante plateforme")
        self.admin_tile = self._build_tile(self.status_strip, "Session")
        self._status_tiles = [self.usb_tile, self.ollama_tile, self.health_tile, self.admin_tile]

        self.kpi_frame = QWidget(self.content)
        self.kpi_layout = QGridLayout(self.kpi_frame)
        self.kpi_layout.setContentsMargins(0, 0, 0, 0)
        self.kpi_layout.setHorizontalSpacing(8)
        self.kpi_layout.setVerticalSpacing(12)
        self.content_layout.addWidget(self.kpi_frame, 3, 0)
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

        self.upper_frame = QWidget(self.content)
        self.upper_layout = QGridLayout(self.upper_frame)
        self.upper_layout.setContentsMargins(0, 0, 0, 0)
        self.upper_layout.setHorizontalSpacing(16)
        self.upper_layout.setVerticalSpacing(12)
        self.content_layout.addWidget(self.upper_frame, 4, 0)

        self.middle_frame = QWidget(self.content)
        self.middle_layout = QGridLayout(self.middle_frame)
        self.middle_layout.setContentsMargins(0, 0, 0, 0)
        self.middle_layout.setHorizontalSpacing(16)
        self.middle_layout.setVerticalSpacing(12)
        self.content_layout.addWidget(self.middle_frame, 5, 0)

        self.bottom_frame = QWidget(self.content)
        self.bottom_layout = QGridLayout(self.bottom_frame)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setHorizontalSpacing(16)
        self.bottom_layout.setVerticalSpacing(12)
        self.content_layout.addWidget(self.bottom_frame, 6, 0)

        events_frame, events_body = self._build_section("Activite recente")
        alerts_frame, alerts_body = self._build_section("Alertes prioritaires")
        health_frame, health_body = self._build_section("Etat des composants")
        brain_frame, brain_body = self._build_section("Moteur d'analyse continu")
        suggestions_frame, suggestions_body = self._build_section("Suggestions supervisees")
        precheck_frame, precheck_body = self._build_section("Precheck demo")

        self._section_frames = {
            "events": events_frame,
            "alerts": alerts_frame,
            "health": health_frame,
            "brain": brain_frame,
            "suggestions": suggestions_frame,
            "precheck": precheck_frame,
        }

        self.event_table = ScrollableTree(events_body, ("date", "type", "summary", "severity"), height=6)
        events_body.layout().addWidget(self.event_table)
        for column, label, width in (
            ("date", "Date", 145),
            ("type", "Type", 120),
            ("summary", "Resume", 360),
            ("severity", "Gravite", 100),
        ):
            self.event_table.tree.heading(column, text=label)
            self.event_table.tree.column(column, width=width, anchor="w")

        self.alert_table = ScrollableTree(alerts_body, ("date", "severity", "title", "score"), height=6)
        alerts_body.layout().addWidget(self.alert_table)
        for column, label, width in (
            ("date", "Date", 145),
            ("severity", "Gravite", 95),
            ("title", "Titre", 260),
            ("score", "Score", 70),
        ):
            self.alert_table.tree.heading(column, text=label)
            self.alert_table.tree.column(column, width=width, anchor="w")

        self.health_table = ScrollableTree(health_body, ("component", "status", "details"), height=4)
        health_body.layout().addWidget(self.health_table)
        for column, label, width in (
            ("component", "Composant", 180),
            ("status", "Etat", 130),
            ("details", "Detail", 520),
        ):
            self.health_table.tree.heading(column, text=label)
            self.health_table.tree.column(column, width=width, anchor="w")

        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL", "INFO", "WARNING", "ERROR", "OK"):
            self.event_table.tree.tag_configure(level, foreground=severity_color(level))
            self.alert_table.tree.tag_configure(level, foreground=severity_color(level))
            self.health_table.tree.tag_configure(level, foreground=severity_color(level))

        brain_layout = QGridLayout(brain_body)
        brain_layout.setContentsMargins(0, 0, 0, 0)
        brain_layout.setHorizontalSpacing(12)
        brain_layout.setVerticalSpacing(12)
        brain_layout.setColumnStretch(0, 1)
        brain_layout.setColumnStretch(1, 1)
        brain_layout.setColumnStretch(2, 1)
        self.brain_summary = QLabel("", brain_body)
        self.brain_summary.setObjectName("muted")
        self.brain_summary.setWordWrap(True)
        brain_layout.addWidget(self.brain_summary, 0, 0, 1, 3)
        badge_row = QWidget(brain_body)
        badge_row_layout = QHBoxLayout(badge_row)
        badge_row_layout.setContentsMargins(0, 0, 0, 0)
        badge_row_layout.setSpacing(8)
        self.brain_level_badge = StatusPill(badge_row, "N/A", "INFO")
        self.brain_progress_badge = StatusPill(badge_row, "STABLE", "INFO")
        badge_row_layout.addWidget(self.brain_level_badge)
        badge_row_layout.addWidget(self.brain_progress_badge)
        badge_row_layout.addStretch(1)
        brain_layout.addWidget(badge_row, 1, 0, 1, 3)
        self.brain_incidents = LabeledValue(brain_body, "Incidents actifs", "-", surface="panel")
        self.brain_alerts = LabeledValue(brain_body, "Alertes ouvertes", "-", surface="panel")
        self.brain_focus = LabeledValue(brain_body, "Points de focus", "-", surface="panel")
        self.brain_new_devices = LabeledValue(brain_body, "Nouveaux 7 jours", "-", surface="panel")
        self.brain_deviations = LabeledValue(brain_body, "Deviations actives", "-", surface="panel")
        self.brain_known = LabeledValue(brain_body, "Parc habituel", "-", surface="panel")
        brain_layout.addWidget(self.brain_incidents, 2, 0)
        brain_layout.addWidget(self.brain_alerts, 2, 1)
        brain_layout.addWidget(self.brain_focus, 2, 2)
        brain_layout.addWidget(self.brain_new_devices, 3, 0)
        brain_layout.addWidget(self.brain_deviations, 3, 1)
        brain_layout.addWidget(self.brain_known, 3, 2)

        suggestions_layout = QGridLayout(suggestions_body)
        suggestions_layout.setContentsMargins(0, 0, 0, 0)
        suggestions_layout.setVerticalSpacing(10)
        suggestion_actions = QWidget(suggestions_body)
        suggestion_actions_layout = QHBoxLayout(suggestion_actions)
        suggestion_actions_layout.setContentsMargins(0, 0, 0, 0)
        suggestion_actions_layout.setSpacing(8)
        suggestion_actions_layout.addStretch(1)
        self.accept_button = QPushButton("Accepter", suggestion_actions)
        self.defer_button = QPushButton("Reporter", suggestion_actions)
        self.defer_button.setObjectName("subtle")
        self.reject_button = QPushButton("Refuser", suggestion_actions)
        self.reject_button.setObjectName("danger")
        self.accept_button.clicked.connect(self._accept_suggestion)
        self.defer_button.clicked.connect(self._defer_suggestion)
        self.reject_button.clicked.connect(self._reject_suggestion)
        suggestion_actions_layout.addWidget(self.accept_button)
        suggestion_actions_layout.addWidget(self.defer_button)
        suggestion_actions_layout.addWidget(self.reject_button)
        suggestions_layout.addWidget(suggestion_actions, 0, 0)
        self.suggestion_table = ScrollableTree(suggestions_body, ("priority", "title", "action", "device"), height=4)
        suggestions_layout.addWidget(self.suggestion_table, 1, 0)
        for column, label, width in (
            ("priority", "Priorite", 110),
            ("title", "Titre", 260),
            ("action", "Action proposee", 180),
            ("device", "Peripherique", 180),
        ):
            self.suggestion_table.tree.heading(column, text=label)
            self.suggestion_table.tree.column(column, width=width, anchor="w")
        self.suggestion_table.tree.bind("<<TreeviewSelect>>", lambda _event: self._sync_suggestion_actions())
        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            self.suggestion_table.tree.tag_configure(level, foreground=severity_color(level))

        precheck_layout = QVBoxLayout(precheck_body)
        precheck_layout.setContentsMargins(0, 0, 0, 0)
        self.precheck_intro = QLabel(
            "Lecture seule. Aucun effet de bord. Utilise les checks existants pour preparer la demo.",
            precheck_body,
        )
        self.precheck_intro.setObjectName("muted")
        self.precheck_intro.setWordWrap(True)
        precheck_layout.addWidget(self.precheck_intro)
        self.precheck_table = ScrollableTree(precheck_body, ("item", "status", "action"), height=4)
        precheck_layout.addWidget(self.precheck_table)
        for column, label, width in (
            ("item", "Point", 170),
            ("status", "Etat", 110),
            ("action", "Action conseillee", 260),
        ):
            self.precheck_table.tree.heading(column, text=label)
            self.precheck_table.tree.column(column, width=width, anchor="w")
        for tone in ("OK", "WARNING", "ERROR"):
            self.precheck_table.tree.tag_configure(tone, foreground=severity_color(tone))

        self._section_wrap_labels.extend([self.brain_summary, self.precheck_intro])
        self._apply_layout("wide")
        self._update_wrap_lengths()

    def refresh_data(self) -> None:
        data = self.controller.get_dashboard_data()
        risk_level = risk_level_from_score(data["global_score"])
        health_map = {status.component: status for status in data["health"]}
        admin_status = health_map.get("admin")
        ollama_status = data["ollama_status"]
        usb_status = data["usb_status"]

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
            self.brain_summary.setText("Le moteur d'analyse n'a pas encore produit de synthese continue.")
            self.brain_incidents.set("-")
            self.brain_alerts.set("-")
            self.brain_focus.set("-")
            self.brain_new_devices.set("-")
            self.brain_deviations.set("-")
            self.brain_known.set("-")
        else:
            progress_tone = {
                "LEARNING": "INFO",
                "STABLE": "OK",
                "IMPROVING": "OK",
                "DETERIORATING": "WARNING",
            }.get(brain_snapshot.progress_status, "INFO")
            self.brain_level_badge.set(brain_snapshot.global_level, brain_snapshot.global_level)
            self.brain_progress_badge.set(brain_snapshot.progress_status, progress_tone)
            self.brain_summary.setText(brain_snapshot.summary)
            self.brain_incidents.set(str(brain_snapshot.open_incident_count))
            self.brain_alerts.set(str(brain_snapshot.open_alert_count))
            self.brain_focus.set(", ".join(brain_snapshot.focus_areas) if brain_snapshot.focus_areas else "Aucun focus prioritaire")
            self.brain_new_devices.set(str(data["new_devices_7d"]))
            self.brain_deviations.set(str(brain_snapshot.deviation_count))
            self.brain_known.set(str(data["known_count"]))

        QTimer.singleShot(0, self.page.force_layout)

    def on_host_resize(self, width: int, height: int) -> None:
        self._dashboard_width = max(width, 1180)
        if width < 1260:
            mode = "compact"
        elif width < 1500:
            mode = "medium"
        else:
            mode = "wide"
        self._apply_layout(mode)
        self._update_wrap_lengths()
        QTimer.singleShot(30, self.page.force_layout)

    def _build_tile(self, parent: QWidget, title: str) -> dict[str, object]:
        frame = QFrame(parent)
        frame.setObjectName("panel")
        layout = QGridLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)
        layout.setColumnStretch(0, 1)
        title_label = QLabel(title, frame)
        title_label.setObjectName("muted")
        layout.addWidget(title_label, 0, 0)
        pill = StatusPill(frame, "", "INFO")
        layout.addWidget(pill, 0, 1)
        value = LabeledValue(frame, "Etat", "-")
        layout.addWidget(value, 1, 0, 1, 2)
        detail = QLabel("", frame)
        detail.setObjectName("muted")
        detail.setWordWrap(True)
        layout.addWidget(detail, 2, 0, 1, 2)
        self._section_wrap_labels.append(detail)
        return {"frame": frame, "value": value, "detail": detail, "pill": pill}

    def _build_section(self, title: str) -> tuple[QGroupBox, QWidget]:
        frame = QGroupBox(title, self.content)
        frame_layout = QVBoxLayout(frame)
        body = QWidget(frame)
        body.setLayout(QVBoxLayout())
        body.layout().setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(body)
        return frame, body

    def _set_tile(self, tile: dict[str, object], value: str, detail: str, tone: str) -> None:
        tile["value"].set(value)
        tile["detail"].setText(detail)
        tile["pill"].set(tone.upper(), tone)

    def _remove_from_layout(self, layout: QGridLayout, widget: QWidget) -> None:
        layout.removeWidget(widget)
        widget.setParent(widget.parentWidget())

    def _apply_layout(self, mode: str) -> None:
        if mode == self._dashboard_mode:
            return
        self._dashboard_mode = mode

        for index in range(5):
            self.kpi_layout.setColumnStretch(index, 0)
        for index in range(4):
            self.status_layout.setColumnStretch(index, 0)
        for layout in (self.upper_layout, self.middle_layout, self.bottom_layout):
            for index in range(3):
                layout.setColumnStretch(index, 0)

        for widget in self._kpi_cards:
            self.kpi_layout.removeWidget(widget)
        for tile in self._status_tiles:
            self.status_layout.removeWidget(tile["frame"])
        for frame in self._section_frames.values():
            self.upper_layout.removeWidget(frame)
            self.middle_layout.removeWidget(frame)
            self.bottom_layout.removeWidget(frame)

        self._section_frames["brain"].setMinimumWidth(0)

        if mode == "compact":
            for index, tile in enumerate(self._status_tiles):
                row = index // 2
                column = index % 2
                self.status_layout.addWidget(tile["frame"], row, column)
                self.status_layout.setColumnStretch(column, 1)
            for index, widget in enumerate(self._kpi_cards):
                row = index // 2
                column = index % 2
                if index == 4:
                    self.kpi_layout.addWidget(widget, 2, 0, 1, 2)
                else:
                    self.kpi_layout.addWidget(widget, row, column)
                self.kpi_layout.setColumnStretch(column, 1)
            self.upper_layout.addWidget(self._section_frames["events"], 0, 0)
            self.upper_layout.addWidget(self._section_frames["alerts"], 1, 0)
            self.middle_layout.addWidget(self._section_frames["health"], 0, 0)
            self.middle_layout.addWidget(self._section_frames["brain"], 1, 0)
            self.bottom_layout.addWidget(self._section_frames["suggestions"], 0, 0)
            self.bottom_layout.addWidget(self._section_frames["precheck"], 1, 0)
            self.upper_layout.setColumnStretch(0, 1)
            self.middle_layout.setColumnStretch(0, 1)
            self.bottom_layout.setColumnStretch(0, 1)
        elif mode == "medium":
            for index, tile in enumerate(self._status_tiles):
                row = index // 2
                column = index % 2
                self.status_layout.addWidget(tile["frame"], row, column)
                self.status_layout.setColumnStretch(column, 1)
            for index, widget in enumerate(self._kpi_cards):
                row = index // 3
                column = index % 3
                self.kpi_layout.addWidget(widget, row, column)
                self.kpi_layout.setColumnStretch(column, 1)
            self.upper_layout.addWidget(self._section_frames["events"], 0, 0)
            self.upper_layout.addWidget(self._section_frames["alerts"], 0, 1)
            self.middle_layout.addWidget(self._section_frames["health"], 0, 0)
            self.middle_layout.addWidget(self._section_frames["brain"], 0, 1)
            self.bottom_layout.addWidget(self._section_frames["suggestions"], 0, 0, 1, 2)
            self.bottom_layout.addWidget(self._section_frames["precheck"], 1, 0, 1, 2)
            self.upper_layout.setColumnStretch(0, 5)
            self.upper_layout.setColumnStretch(1, 4)
            self.middle_layout.setColumnStretch(0, 6)
            self.middle_layout.setColumnStretch(1, 4)
            self.bottom_layout.setColumnStretch(0, 1)
            self.bottom_layout.setColumnStretch(1, 1)
            self._section_frames["brain"].setMinimumWidth(360)
        else:
            for index, tile in enumerate(self._status_tiles):
                self.status_layout.addWidget(tile["frame"], 0, index)
                self.status_layout.setColumnStretch(index, 1)
            for index, widget in enumerate(self._kpi_cards):
                self.kpi_layout.addWidget(widget, 0, index)
                self.kpi_layout.setColumnStretch(index, 1)
            self.upper_layout.addWidget(self._section_frames["events"], 0, 0)
            self.upper_layout.addWidget(self._section_frames["alerts"], 0, 1)
            self.middle_layout.addWidget(self._section_frames["health"], 0, 0)
            self.middle_layout.addWidget(self._section_frames["brain"], 0, 1)
            self.bottom_layout.addWidget(self._section_frames["suggestions"], 0, 0)
            self.bottom_layout.addWidget(self._section_frames["precheck"], 0, 1)
            self.upper_layout.setColumnStretch(0, 5)
            self.upper_layout.setColumnStretch(1, 5)
            self.middle_layout.setColumnStretch(0, 7)
            self.middle_layout.setColumnStretch(1, 4)
            self.bottom_layout.setColumnStretch(0, 5)
            self.bottom_layout.setColumnStretch(1, 4)
            self._section_frames["brain"].setMinimumWidth(380)

        self._update_wrap_lengths()

    def _update_wrap_lengths(self) -> None:
        if self._dashboard_width < 1320:
            tile_wrap = 170
            summary_wrap = 420
            precheck_wrap = 420
            event_height = 5
            side_height = 4
        elif self._dashboard_width < 1520:
            tile_wrap = 210
            summary_wrap = 520
            precheck_wrap = 500
            event_height = 5
            side_height = 4
        else:
            tile_wrap = 250
            summary_wrap = 620
            precheck_wrap = 560
            event_height = 6
            side_height = 4

        for tile in self._status_tiles:
            tile["detail"].setMaximumWidth(tile_wrap)
        self.brain_summary.setMaximumWidth(16777215)
        self.precheck_intro.setMaximumWidth(16777215)
        self.event_table.tree.configure(height=event_height)
        self.alert_table.tree.configure(height=event_height)
        self.health_table.tree.configure(height=side_height)
        self.suggestion_table.tree.configure(height=side_height)
        self.precheck_table.tree.configure(height=side_height)

    def reset_scroll_position(self) -> None:
        self.page.scroll_to_top()

    def _selected_suggestion(self):
        selection = self.suggestion_table.tree.selection()
        if not selection:
            return None
        return self._suggestion_rows.get(selection[0])

    def _sync_suggestion_actions(self) -> None:
        enabled = self._selected_suggestion() is not None
        self.accept_button.setEnabled(enabled)
        self.defer_button.setEnabled(enabled)
        self.reject_button.setEnabled(enabled)

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
