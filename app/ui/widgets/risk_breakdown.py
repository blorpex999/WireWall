from __future__ import annotations

import logging

from PyQt6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget

from app.models.entities import RiskAssessment
from app.ui.theme import COLORS

LOGGER = logging.getLogger(__name__)

POSITIVE_REASON_KEYWORDS = (
    "whitelist",
    "connu",
    "habituel",
    "reduit",
    "stable",
    "decision analyste",
)


def _surface_bg(surface: str) -> str:
    return {
        "page": COLORS["bg"],
        "panel": COLORS["panel"],
        "panel_alt": COLORS["panel_alt"],
    }.get(surface, COLORS["panel"])


class RiskBreakdownWidget(QFrame):
    def __init__(self, parent: QWidget | None = None, surface: str = "panel") -> None:
        super().__init__(parent)
        self._bg = _surface_bg(surface)
        self._assessment: RiskAssessment | None = None
        self.setStyleSheet(f"background-color: {self._bg};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.empty_label = QLabel("Aucun score disponible pour ce peripherique.", self)
        self.empty_label.setObjectName("muted")
        layout.addWidget(self.empty_label)

        self.score_bar = QProgressBar(self)
        self.score_bar.setRange(0, 100)
        self.score_bar.setTextVisible(True)
        self.score_bar.hide()
        layout.addWidget(self.score_bar)

        self.reasons_text = QLabel(self)
        self.reasons_text.setWordWrap(True)
        self.reasons_text.hide()
        layout.addWidget(self.reasons_text)

        self.recommendations_title = QLabel("Actions recommandees", self)
        self.recommendations_title.setObjectName("muted")
        self.recommendations_title.hide()
        layout.addWidget(self.recommendations_title)

        self.recommendations_text = QLabel(self)
        self.recommendations_text.setObjectName("muted")
        self.recommendations_text.setWordWrap(True)
        self.recommendations_text.hide()
        layout.addWidget(self.recommendations_text)

    def set_assessment(self, assessment: RiskAssessment | None) -> None:
        self._assessment = assessment
        if assessment is None:
            self.empty_label.show()
            self.score_bar.hide()
            self.reasons_text.hide()
            self.recommendations_title.hide()
            self.recommendations_text.hide()
            return

        self.empty_label.hide()
        score = max(0, min(100, int(assessment.score)))
        bar_color = self._score_color(score)
        self.score_bar.setStyleSheet(
            "QProgressBar {{ background-color: {track}; border: 1px solid {border}; border-radius: 6px; text-align: center; }}"
            "QProgressBar::chunk {{ background-color: {chunk}; border-radius: 6px; }}".format(
                track=COLORS["panel_alt"],
                border=COLORS["panel_border"],
                chunk=bar_color,
            )
        )
        self.score_bar.setValue(score)
        self.score_bar.setFormat(f"Score : {score} / 100 - {assessment.level}")
        self.score_bar.show()

        reasons = assessment.reasons or ["Aucune raison detaillee disponible."]
        formatted_reasons = "\n".join(f"{self._reason_prefix(reason, assessment.level)} {reason}" for reason in reasons)
        self.reasons_text.setText(formatted_reasons)
        self.reasons_text.show()

        if assessment.recommendations:
            self.recommendations_title.show()
            self.recommendations_text.setText("\n".join(f"- {item}" for item in assessment.recommendations))
            self.recommendations_text.show()
        else:
            self.recommendations_title.hide()
            self.recommendations_text.hide()

    def _reason_prefix(self, reason: str, level: str) -> str:
        normalized = reason.lower()
        if any(keyword in normalized for keyword in POSITIVE_REASON_KEYWORDS):
            return "[+]"
        if level.upper() in {"HIGH", "CRITICAL"}:
            return "[x]"
        return "[!]"

    def _score_color(self, score: int) -> str:
        if score <= 30:
            return COLORS["success"]
        if score <= 55:
            return COLORS["warning"]
        if score <= 75:
            return COLORS["danger_soft"]
        return COLORS["danger"]
