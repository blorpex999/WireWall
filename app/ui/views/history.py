from __future__ import annotations

from PyQt6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.ui.views.base import BaseView
from app.ui.widgets.common import LabeledValue, ScrollableDetailText, ScrollablePage, ScrollableTree, SectionHeader, StatusPill
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

    def __init__(self, parent, controller, app) -> None:
        super().__init__(parent, controller, app)
        self._rows: dict[str, object] = {}
        self._selected_event_key: str | None = None

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(12)
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 2)
        layout.setRowStretch(2, 1)

        self.header = SectionHeader(
            self,
            "Historique et audit",
            "Trace horodatee des evenements USB, des anomalies de scan et des exports d'audit.",
        )
        layout.addWidget(self.header, 0, 0, 1, 2)

        toolbar = QGroupBox("Filtres et exports", self)
        toolbar_layout = QGridLayout(toolbar)
        toolbar_layout.setHorizontalSpacing(12)
        toolbar_layout.setVerticalSpacing(12)
        toolbar_layout.setColumnStretch(1, 1)
        toolbar_layout.setColumnStretch(3, 1)
        layout.addWidget(toolbar, 1, 0, 1, 2)

        toolbar_layout.addWidget(QLabel("Recherche", toolbar), 0, 0)
        self.search_entry = QLineEdit(toolbar)
        toolbar_layout.addWidget(self.search_entry, 0, 1)

        toolbar_layout.addWidget(QLabel("Gravite", toolbar), 0, 2)
        self.severity_combo = QComboBox(toolbar)
        self.severity_combo.addItems(list(self.SEVERITY_OPTIONS.keys()))
        toolbar_layout.addWidget(self.severity_combo, 0, 3)

        apply_button = QPushButton("Appliquer", toolbar)
        apply_button.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(apply_button, 1, 2)

        actions = QWidget(toolbar)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        csv_button = QPushButton("CSV", actions)
        json_button = QPushButton("JSON", actions)
        html_button = QPushButton("Rapport HTML", actions)
        csv_button.clicked.connect(lambda: self._export("csv"))
        json_button.clicked.connect(lambda: self._export("json"))
        html_button.clicked.connect(lambda: self._export("html"))
        actions_layout.addWidget(csv_button)
        actions_layout.addWidget(json_button)
        actions_layout.addWidget(html_button)
        actions_layout.addStretch(1)
        toolbar_layout.addWidget(actions, 1, 3)

        self.search_entry.textChanged.connect(lambda _text: self.schedule_refresh(250))
        self.search_entry.returnPressed.connect(self.refresh_data)
        self.severity_combo.currentTextChanged.connect(lambda _text: self.refresh_data())

        list_frame = QGroupBox("Evenements", self)
        list_layout = QVBoxLayout(list_frame)
        detail_frame = QGroupBox("Detail d'audit", self)
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_page = ScrollablePage(detail_frame)
        detail_layout.addWidget(self.detail_page)
        detail_body = QWidget(self.detail_page.body)
        self.detail_page.body_layout.addWidget(detail_body)
        detail_layout = QVBoxLayout(detail_body)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(12)
        layout.addWidget(list_frame, 2, 0)
        layout.addWidget(detail_frame, 2, 1)

        self.table = ScrollableTree(list_frame, ("date", "type", "device", "summary", "severity"), height=18)
        list_layout.addWidget(self.table)
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

        top = QWidget(detail_frame)
        top.setObjectName("card")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(12, 12, 12, 12)
        top_layout.addWidget(QLabel("Resume de l'evenement", top), 1)
        self.severity_badge = StatusPill(top, "INFO", "INFO")
        top_layout.addWidget(self.severity_badge)
        detail_layout.addWidget(top)

        metrics = QWidget(detail_frame)
        metrics.setObjectName("card")
        metrics_layout = QGridLayout(metrics)
        metrics_layout.setContentsMargins(12, 12, 12, 12)
        metrics_layout.setHorizontalSpacing(10)
        metrics_layout.setVerticalSpacing(8)
        metrics_layout.setColumnStretch(0, 1)
        metrics_layout.setColumnStretch(1, 1)
        detail_layout.addWidget(metrics)
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
            metrics_layout.addWidget(self.values[key], row, column)

        self.detail_text = ScrollableDetailText(detail_frame, height=18)
        detail_layout.addWidget(self.detail_text, 1)
        self._clear_selection_state()

    def refresh_data(self) -> None:
        severity = self.SEVERITY_OPTIONS[self.severity_combo.currentText()]
        selected_key = self._get_selected_event_key() or self._selected_event_key
        events = self.controller.list_events(self.search_entry.text().strip(), severity)
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
        previous_key = self._selected_event_key
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
        if self._selected_event_key != previous_key:
            self.detail_page.scroll_to_top()

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

    def reset_scroll_position(self) -> None:
        self.detail_page.scroll_to_top()
