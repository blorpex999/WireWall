from __future__ import annotations

from PyQt6.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.help_content import SCREEN_HELP
from app.ui.views.base import BaseView
from app.ui.widgets.common import (
    InlineHelpPanel,
    LabeledValue,
    ScrollableDetailText,
    ScrollablePage,
    ScrollableTree,
    SectionHeader,
    StatusPill,
)
from app.utils.datetime import format_for_ui
from app.utils.ui import health_status_text, severity_color, shorten_text, tone_for_status


class AIAnalysisView(BaseView):
    view_title = "Analyse IA"

    def __init__(self, parent, controller, app) -> None:
        super().__init__(parent, controller, app)
        self._rows: dict[str, object] = {}
        self._selected_analysis_key: str | None = None

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(12)
        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 3)
        layout.setRowStretch(3, 1)

        self.header = SectionHeader(
            self,
            "Analyse IA locale",
            "Analyse contextuelle des appareils, evenements et alertes via Ollama sur localhost.",
            "LOCAL",
            "INFO",
        )
        layout.addWidget(self.header, 0, 0, 1, 2)

        self.help_panel = InlineHelpPanel(
            self,
            button_text=str(SCREEN_HELP["ai_analysis"]["button"]),
            sections=list(SCREEN_HELP["ai_analysis"]["sections"]),
        )
        layout.addWidget(self.help_panel, 1, 0, 1, 2)

        top = QGroupBox("Etat et lancement", self)
        top_layout = QGridLayout(top)
        top_layout.setHorizontalSpacing(12)
        top_layout.setVerticalSpacing(10)
        top_layout.setColumnStretch(1, 1)
        top_layout.setColumnStretch(3, 1)
        layout.addWidget(top, 2, 0, 1, 2)

        top_layout.addWidget(QLabel("Modele", top), 0, 0)
        self.model_value = LabeledValue(top, "Modele IA", "-", surface="page")
        top_layout.addWidget(self.model_value, 0, 1)

        top_layout.addWidget(QLabel("Etat Ollama", top), 0, 2)
        badge_box = QWidget(top)
        badge_layout = QHBoxLayout(badge_box)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        self.ollama_badge = StatusPill(badge_box, "INCONNU", "INFO")
        badge_layout.addWidget(self.ollama_badge)
        badge_layout.addStretch(1)
        top_layout.addWidget(badge_box, 0, 3)

        self.ollama_detail = QLabel("", top)
        self.ollama_detail.setObjectName("muted")
        self.ollama_detail.setWordWrap(True)
        top_layout.addWidget(self.ollama_detail, 1, 0, 1, 4)

        self.local_note = QLabel(
            "Analyse locale uniquement. Ollama doit etre disponible sur localhost. L'IA propose et n'agit jamais seule.",
            top,
        )
        self.local_note.setObjectName("muted")
        self.local_note.setWordWrap(True)
        top_layout.addWidget(self.local_note, 2, 0, 1, 4)

        self.run_button = QPushButton("Lancer l'analyse locale", top)
        self.run_button.clicked.connect(self._run_analysis)
        top_layout.addWidget(self.run_button, 0, 4, 3, 1)

        list_frame = QGroupBox("Analyses recentes", self)
        list_layout = QVBoxLayout(list_frame)
        detail_frame = QGroupBox("Lecture analyste", self)
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_page = ScrollablePage(detail_frame)
        detail_layout.addWidget(self.detail_page)
        detail_body = QWidget(self.detail_page.body)
        self.detail_page.body_layout.addWidget(detail_body)
        detail_layout = QVBoxLayout(detail_body)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(12)
        layout.addWidget(list_frame, 3, 0)
        layout.addWidget(detail_frame, 3, 1)

        self.table = ScrollableTree(list_frame, ("date", "model", "level", "success"), height=18)
        list_layout.addWidget(self.table)
        for column, label, width in (
            ("date", "Date", 150),
            ("model", "Modele", 140),
            ("level", "Niveau", 90),
            ("success", "Succes", 90),
        ):
            self.table.tree.heading(column, text=label)
            self.table.tree.column(column, width=width, anchor="w")
        self.table.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_selected())
        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL", "INFO", "WARNING", "ERROR"):
            self.table.tree.tag_configure(level, foreground=severity_color(level))

        top_detail = QWidget(detail_frame)
        top_detail.setObjectName("card")
        top_detail_layout = QHBoxLayout(top_detail)
        top_detail_layout.setContentsMargins(12, 12, 12, 12)
        synth_label = QLabel("Synthese de l'analyse", top_detail)
        synth_label.setObjectName("muted")
        top_detail_layout.addWidget(synth_label, 1)
        self.level_badge = StatusPill(top_detail, "N/A", "INFO")
        top_detail_layout.addWidget(self.level_badge)
        detail_layout.addWidget(top_detail)

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
            "model": LabeledValue(metrics, "Modele"),
            "level": LabeledValue(metrics, "Niveau"),
            "success": LabeledValue(metrics, "Succes"),
        }
        metrics_layout.addWidget(self.values["date"], 0, 0)
        metrics_layout.addWidget(self.values["model"], 0, 1)
        metrics_layout.addWidget(self.values["level"], 1, 0)
        metrics_layout.addWidget(self.values["success"], 1, 1)

        summary_frame = QGroupBox("Resume", detail_frame)
        summary_layout = QVBoxLayout(summary_frame)
        self.summary_text = ScrollableDetailText(summary_frame, height=6)
        summary_layout.addWidget(self.summary_text)
        detail_layout.addWidget(summary_frame)

        threats_frame = QGroupBox("Anomalies probables", detail_frame)
        threats_layout = QVBoxLayout(threats_frame)
        self.threats_text = ScrollableDetailText(threats_frame, height=6)
        threats_layout.addWidget(self.threats_text)
        detail_layout.addWidget(threats_frame)

        recos_frame = QGroupBox("Recommandations", detail_frame)
        recos_layout = QVBoxLayout(recos_frame)
        self.recommendations_text = ScrollableDetailText(recos_frame, height=7)
        recos_layout.addWidget(self.recommendations_text)
        detail_layout.addWidget(recos_frame, 1)

        self._clear_selection_state()

    def refresh_data(self) -> None:
        analyses = self.controller.list_ai_analyses()
        health = self.controller.get_ollama_health_status()
        selected_key = self._get_selected_analysis_key() or self._selected_analysis_key
        self.model_value.set(self.controller.settings.ollama_model)
        self.ollama_badge.set(health_status_text(health.status).upper(), tone_for_status(health.status))
        self.ollama_detail.setText(shorten_text(health.details, 120))
        self.run_button.setEnabled(not self.controller.is_task_running("ai_analysis"))

        self._rows.clear()
        self.table.clear()
        item_to_restore: str | None = None
        for analysis in analyses:
            analysis_key = self._analysis_key(analysis)
            item_id = self.table.tree.insert(
                "",
                "end",
                values=(format_for_ui(analysis.created_at), analysis.model, analysis.global_level, "Oui" if analysis.success else "Non"),
                tags=(analysis.global_level,),
            )
            self._rows[item_id] = analysis
            if analysis_key == selected_key:
                item_to_restore = item_id
        self.table.set_empty(bool(analyses), "Aucune analyse IA n'a encore ete lancee.")
        if item_to_restore is not None:
            self.table.tree.selection_set(item_to_restore)
            self.table.tree.focus(item_to_restore)
            self.table.tree.see(item_to_restore)
            self._show_selected()
        else:
            self._clear_selection_state()

    def _run_analysis(self) -> None:
        started = self.controller.request_ai_analysis()
        if not started:
            self.app.set_status("Une analyse IA est deja en cours.", "WARNING")
            return
        self.refresh_data()
        self.app.set_status("Analyse IA locale lancee en arriere-plan.", "INFO")

    def _show_selected(self) -> None:
        selection = self.table.tree.selection()
        if not selection:
            self._clear_selection_state()
            return
        analysis = self._rows.get(selection[0])
        if analysis is None:
            self._clear_selection_state()
            return
        self._selected_analysis_key = self._analysis_key(analysis)
        self.level_badge.set(analysis.global_level, analysis.global_level)
        self.values["date"].set(format_for_ui(analysis.created_at))
        self.values["model"].set(analysis.model)
        self.values["level"].set(analysis.global_level)
        self.values["success"].set("Oui" if analysis.success else "Non")
        self.summary_text.set_text(analysis.summary or "Aucun resume disponible.")
        self.threats_text.set_text("\n- ".join(["Anomalies"] + (analysis.threats or ["Aucune anomalie detaillee."])))
        self.recommendations_text.set_text(
            "\n- ".join(["Recommandations"] + (analysis.recommendations or ["Aucune recommandation detaillee."]))
        )
        self.detail_page.scroll_to_top()

    def _clear_selection_state(self) -> None:
        self._selected_analysis_key = None
        self.level_badge.set("N/A", "INFO")
        for value in self.values.values():
            value.set("-")
        self.summary_text.set_text("Selectionnez une analyse pour afficher le resume genere localement.")
        self.threats_text.set_text("Anomalies\n- Aucune analyse selectionnee.")
        self.recommendations_text.set_text("Recommandations\n- Aucune analyse selectionnee.")

    def _get_selected_analysis_key(self) -> str | None:
        selection = self.table.tree.selection()
        if not selection:
            return None
        analysis = self._rows.get(selection[0])
        if analysis is None:
            return None
        return self._analysis_key(analysis)

    def _analysis_key(self, analysis) -> str:
        if getattr(analysis, "id", None) is not None:
            return f"id:{analysis.id}"
        return f"{analysis.created_at}|{analysis.model}|{analysis.global_level}"

    def reset_scroll_position(self) -> None:
        self.detail_page.scroll_to_top()
