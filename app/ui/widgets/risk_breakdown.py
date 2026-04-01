from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk

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
    "d\u00e9cision analyste",
)


def _surface_bg(surface: str) -> str:
    return {
        "page": COLORS["bg"],
        "panel": COLORS["panel"],
        "panel_alt": COLORS["panel_alt"],
    }.get(surface, COLORS["panel"])


class RiskBreakdownWidget(ttk.Frame):
    def __init__(self, master, surface: str = "panel") -> None:
        super().__init__(master)
        self._bg = _surface_bg(surface)
        self._assessment: RiskAssessment | None = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.body = tk.Frame(self, bg=self._bg, bd=0, highlightthickness=0)
        self.body.grid(row=0, column=0, sticky="nsew")
        self.body.columnconfigure(0, weight=1)

        self.empty_label = tk.Label(
            self.body,
            text="Aucun score disponible pour ce peripherique.",
            bg=self._bg,
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
        )
        self.empty_label.grid(row=0, column=0, sticky="ew")

        self.score_canvas = tk.Canvas(
            self.body,
            height=28,
            bg=self._bg,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.score_canvas.bind("<Configure>", self._on_score_configure)

        self.reasons_text = tk.Text(
            self.body,
            height=5,
            bg=self._bg,
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            highlightthickness=1,
            highlightbackground=COLORS["panel_border"],
            relief="flat",
            wrap="word",
            padx=8,
            pady=8,
            font=("Segoe UI", 10),
        )
        self.reasons_text.tag_configure("reason", foreground=COLORS["text"])
        self.reasons_text.tag_configure("positive", foreground=COLORS["success"])
        self.reasons_text.tag_configure("warning", foreground=COLORS["warning"])
        self.reasons_text.tag_configure("danger", foreground=COLORS["danger"])
        self.reasons_text.configure(state="disabled")

        self.recommendations_title = tk.Label(
            self.body,
            text="Actions recommandees",
            bg=self._bg,
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.recommendations_text = tk.Text(
            self.body,
            height=3,
            bg=self._bg,
            fg=COLORS["muted"],
            insertbackground=COLORS["muted"],
            highlightthickness=1,
            highlightbackground=COLORS["panel_border"],
            relief="flat",
            wrap="word",
            padx=8,
            pady=8,
            font=("Segoe UI", 9, "italic"),
        )
        self.recommendations_text.tag_configure("recommendation", foreground=COLORS["muted"])
        self.recommendations_text.configure(state="disabled")

    def update(self, assessment: RiskAssessment | None) -> None:
        self._assessment = assessment
        if assessment is None:
            self._clear_text(self.reasons_text)
            self._clear_text(self.recommendations_text)
            self.score_canvas.delete("all")
            self.score_canvas.grid_remove()
            self.reasons_text.grid_remove()
            self.recommendations_title.grid_remove()
            self.recommendations_text.grid_remove()
            self.empty_label.grid(row=0, column=0, sticky="ew")
            return

        self.empty_label.grid_remove()
        self.score_canvas.grid(row=0, column=0, sticky="ew")
        self.reasons_text.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self._draw_score_bar()
        self._render_reasons(assessment)

        if assessment.recommendations:
            self.recommendations_title.grid(row=2, column=0, sticky="w", pady=(10, 0))
            self.recommendations_text.grid(row=3, column=0, sticky="ew", pady=(4, 0))
            self._render_recommendations(assessment.recommendations)
        else:
            self._clear_text(self.recommendations_text)
            self.recommendations_title.grid_remove()
            self.recommendations_text.grid_remove()

    def _on_score_configure(self, _event: tk.Event) -> None:
        if self._assessment is not None:
            self._draw_score_bar()

    def _draw_score_bar(self) -> None:
        assessment = self._assessment
        if assessment is None:
            self.score_canvas.delete("all")
            return

        width = max(self.score_canvas.winfo_width(), 1)
        height = 28
        score = max(0, min(100, int(assessment.score)))
        fill_width = int(width * (score / 100))

        self.score_canvas.delete("all")
        self.score_canvas.create_rectangle(0, 0, width, height, fill=COLORS["panel_alt"], outline="")
        if fill_width > 0:
            self.score_canvas.create_rectangle(0, 0, fill_width, height, fill=self._score_color(score), outline="")
        self.score_canvas.create_text(
            width / 2,
            height / 2,
            text=f"Score : {score} / 100 \u2014 {assessment.level}",
            fill=COLORS["text"],
            font=("Segoe UI Semibold", 10),
        )

    def _render_reasons(self, assessment: RiskAssessment) -> None:
        self._clear_text(self.reasons_text)
        self.reasons_text.configure(state="normal", height=max(4, min(8, len(assessment.reasons) or 1)))
        for reason in assessment.reasons or ["Aucune raison detaillee disponible."]:
            prefix, tag = self._reason_prefix(reason, assessment.level)
            self.reasons_text.insert("end", prefix, tag)
            self.reasons_text.insert("end", f"{reason}\n", "reason")
        self.reasons_text.configure(state="disabled")

    def _render_recommendations(self, recommendations: list[str]) -> None:
        self._clear_text(self.recommendations_text)
        self.recommendations_text.configure(state="normal", height=max(2, min(5, len(recommendations))))
        for recommendation in recommendations:
            self.recommendations_text.insert("end", f"- {recommendation}\n", "recommendation")
        self.recommendations_text.configure(state="disabled")

    def _clear_text(self, widget: tk.Text) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.configure(state="disabled")

    def _reason_prefix(self, reason: str, level: str) -> tuple[str, str]:
        normalized = reason.lower()
        if any(keyword in normalized for keyword in POSITIVE_REASON_KEYWORDS):
            return "\u2713 ", "positive"
        if level.upper() in {"HIGH", "CRITICAL"}:
            return "\u2717 ", "danger"
        return "\u26A0 ", "warning"

    def _score_color(self, score: int) -> str:
        if score <= 30:
            return COLORS["success"]
        if score <= 55:
            return COLORS["warning"]
        if score <= 75:
            return COLORS["danger_soft"]
        return COLORS["danger"]
