from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.controller import AppController
from app.ui.theme import COLORS
from app.ui.widgets.common import LabeledValue, ScrollablePage, StatusPill
from app.ui.widgets.risk_breakdown import RiskBreakdownWidget
from app.utils.datetime import parse_timestamp
from app.utils.ui import category_text, decision_text, severity_color, shorten_text, trust_state_text, trust_state_tone

LOGGER = logging.getLogger(__name__)


class InvestigationWindow(QDialog):
    def __init__(self, parent: QWidget | None, controller: AppController, device_key: str) -> None:
        super().__init__(parent)
        self.controller = controller
        self.device_key = device_key

        self.setWindowTitle(f"WireWall - Enquete : {device_key}")
        self.resize(920, 680)
        self.setMinimumSize(720, 500)
        self.setModal(False)
        self.setWindowFlag(Qt.WindowType.Window, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.page = ScrollablePage(self)
        layout.addWidget(self.page)

        self.content = QWidget(self.page.body)
        self.page.body_layout.addWidget(self.content)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(18, 18, 18, 18)
        self.content_layout.setSpacing(12)

        device = self.controller.get_device(device_key)
        if device is None:
            LOGGER.warning("Ouverture d'enquete impossible, device introuvable: %s", device_key)
            missing = QGroupBox("Peripherique", self.content)
            missing_layout = QVBoxLayout(missing)
            label = QLabel("Peripherique introuvable en base.", missing)
            label.setObjectName("muted")
            missing_layout.addWidget(label)
            self.content_layout.addWidget(missing)
            close_button = QPushButton("Fermer", self.content)
            close_button.setObjectName("subtle")
            close_button.clicked.connect(self.close)
            self.content_layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)
            return

        identity = QGroupBox("Peripherique", self.content)
        identity_layout = QGridLayout(identity)
        identity_layout.setColumnStretch(0, 1)
        identity_layout.setColumnStretch(1, 1)
        identity_layout.setColumnStretch(2, 1)
        identity_layout.setColumnStretch(3, 1)
        self.content_layout.addWidget(identity)

        identity_layout.addWidget(LabeledValue(identity, "VID:PID", device.vid_pid), 0, 0)
        identity_layout.addWidget(LabeledValue(identity, "Fabricant", device.vendor_name or "-"), 0, 1)
        identity_layout.addWidget(LabeledValue(identity, "Produit", device.product_name or "-"), 0, 2)
        identity_layout.addWidget(LabeledValue(identity, "Numero de serie", device.serial_number or "-"), 0, 3)
        identity_layout.addWidget(LabeledValue(identity, "Categorie", category_text(device.category)), 1, 0)

        trust_cell = QWidget(identity)
        trust_layout = QHBoxLayout(trust_cell)
        trust_layout.setContentsMargins(0, 0, 0, 0)
        trust_layout.setSpacing(10)
        self.trust_value = LabeledValue(trust_cell, "Trust state", trust_state_text(device.trust_state))
        trust_layout.addWidget(self.trust_value, 1)
        self.trust_badge = StatusPill(trust_cell, trust_state_text(device.trust_state).upper(), trust_state_tone(device.trust_state))
        trust_layout.addWidget(self.trust_badge)
        identity_layout.addWidget(trust_cell, 1, 1)
        identity_layout.addWidget(LabeledValue(identity, "Seen count", str(device.seen_count)), 1, 2)
        identity_layout.addWidget(LabeledValue(identity, "Derniere decision", decision_text(device.last_decision)), 1, 3)

        timeline = QGroupBox("Timeline des evenements", self.content)
        timeline_layout = QVBoxLayout(timeline)
        self.content_layout.addWidget(timeline)

        self.timeline_host = QWidget(timeline)
        self.timeline_host_layout = QVBoxLayout(self.timeline_host)
        self.timeline_host_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_host_layout.setSpacing(0)
        timeline_layout.addWidget(self.timeline_host)
        self._render_timeline()

        assessment_frame = QGroupBox("Analyse de risque", self.content)
        assessment_layout = QVBoxLayout(assessment_frame)
        self.content_layout.addWidget(assessment_frame)
        self.risk_widget = RiskBreakdownWidget(assessment_frame, surface="panel")
        assessment_layout.addWidget(self.risk_widget)
        self.risk_widget.set_assessment(self.controller.container.assessment_repo.latest(device_key))

        footer = QWidget(self.content)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.addStretch(1)
        close_button = QPushButton("Fermer", footer)
        close_button.setObjectName("subtle")
        close_button.clicked.connect(self.close)
        footer_layout.addWidget(close_button)
        self.content_layout.addWidget(footer)

    def _render_timeline(self) -> None:
        while self.timeline_host_layout.count():
            item = self.timeline_host_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        events = sorted(
            self.controller.get_device_history(self.device_key, limit=100),
            key=lambda event: event.occurred_at,
            reverse=True,
        )
        if not events:
            label = QLabel("Aucun evenement enregistre pour ce peripherique.", self.timeline_host)
            label.setObjectName("muted")
            self.timeline_host_layout.addWidget(label)
            return

        for index, event in enumerate(events):
            row = QFrame(self.timeline_host)
            row.setStyleSheet(
                "background-color: {bg}; padding: 10px 12px;".format(
                    bg=COLORS["panel"] if index % 2 == 0 else COLORS["panel_alt"],
                )
            )
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(10)

            time_label = QLabel(self._timeline_time(event.occurred_at), row)
            time_label.setObjectName("muted")
            row_layout.addWidget(time_label)

            dot = QLabel("o", row)
            dot.setStyleSheet(f"color: {severity_color(event.severity)}; font-size: 11pt;")
            row_layout.addWidget(dot)

            type_label = QLabel(event.event_type, row)
            type_label.setStyleSheet("font-weight: 600;")
            row_layout.addWidget(type_label)

            summary_label = QLabel(shorten_text(event.summary, 80), row)
            summary_label.setWordWrap(True)
            row_layout.addWidget(summary_label, 1)

            row_layout.addWidget(StatusPill(row, event.severity, event.severity))
            self.timeline_host_layout.addWidget(row)
        self.timeline_host_layout.addStretch(1)

    def _timeline_time(self, value: str | None) -> str:
        parsed = parse_timestamp(value)
        if parsed is None:
            return "--:--:--  --/--"
        return parsed.astimezone().strftime("%H:%M:%S  %d/%m")
