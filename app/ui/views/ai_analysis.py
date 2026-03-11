from __future__ import annotations

from tkinter import ttk

from app.ui.views.base import BaseView
from app.ui.widgets.common import LabeledValue, ScrollableDetailText, ScrollableTree, SectionHeader, StatusPill
from app.utils.datetime import format_for_ui
from app.utils.ui import health_status_text, severity_color, shorten_text, tone_for_status


class AIAnalysisView(BaseView):
    view_title = "Analyse IA"

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(2, weight=1)
        self._rows: dict[str, object] = {}

        self.header = SectionHeader(
            self,
            "Analyse IA locale",
            "Analyse contextuelle des appareils, evenements et alertes via Ollama sur localhost.",
            "LOCAL",
            "INFO",
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        top = ttk.LabelFrame(self, text="Etat et lancement", style="Section.TLabelframe", padding=12)
        top.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        top.columnconfigure(1, weight=1)
        top.columnconfigure(3, weight=1)
        ttk.Label(top, text="Modele").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.model_value = LabeledValue(top, "Modele IA", "-")
        self.model_value.grid(row=0, column=1, sticky="w")
        ttk.Label(top, text="Etat Ollama").grid(row=0, column=2, sticky="w", padx=(24, 8))
        badge_box = ttk.Frame(top)
        badge_box.grid(row=0, column=3, sticky="w")
        self.ollama_badge = StatusPill(badge_box, "INCONNU", "INFO")
        self.ollama_badge.pack(side="left")
        self.ollama_detail = ttk.Label(top, text="", style="Muted.TLabel", wraplength=520, justify="left")
        self.ollama_detail.grid(row=1, column=0, columnspan=4, sticky="w", pady=(10, 0))
        self.run_button = ttk.Button(top, text="Lancer l'analyse locale", style="Accent.TButton", command=self._run_analysis)
        self.run_button.grid(row=0, column=4, rowspan=2, sticky="e")

        list_frame = ttk.LabelFrame(self, text="Analyses recentes", style="Section.TLabelframe", padding=12)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        detail_frame = ttk.LabelFrame(self, text="Lecture analyste", style="Section.TLabelframe", padding=12)
        detail_frame.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(4, weight=1)

        self.table = ScrollableTree(list_frame, ("date", "model", "level", "success"), height=18)
        self.table.pack(fill="both", expand=True)
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

        top_detail = ttk.Frame(detail_frame, style="Card.TFrame", padding=12)
        top_detail.grid(row=0, column=0, sticky="ew")
        top_detail.columnconfigure(0, weight=1)
        ttk.Label(top_detail, text="Synthese de l'analyse", style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
        self.level_badge = StatusPill(top_detail, "N/A", "INFO")
        self.level_badge.grid(row=0, column=1, sticky="e")

        metrics = ttk.Frame(detail_frame, style="Card.TFrame", padding=12)
        metrics.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        for column in range(2):
            metrics.columnconfigure(column, weight=1)
        self.values = {
            "date": LabeledValue(metrics, "Date"),
            "model": LabeledValue(metrics, "Modele"),
            "level": LabeledValue(metrics, "Niveau"),
            "success": LabeledValue(metrics, "Succes"),
        }
        self.values["date"].grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=6)
        self.values["model"].grid(row=0, column=1, sticky="ew", pady=6)
        self.values["level"].grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=6)
        self.values["success"].grid(row=1, column=1, sticky="ew", pady=6)

        summary_frame = ttk.LabelFrame(detail_frame, text="Resume", style="Section.TLabelframe", padding=8)
        summary_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.summary_text = ScrollableDetailText(summary_frame, height=6)
        self.summary_text.pack(fill="both", expand=True)

        threats_frame = ttk.LabelFrame(detail_frame, text="Menaces probables", style="Section.TLabelframe", padding=8)
        threats_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        self.threats_text = ScrollableDetailText(threats_frame, height=6)
        self.threats_text.pack(fill="both", expand=True)

        recos_frame = ttk.LabelFrame(detail_frame, text="Recommandations", style="Section.TLabelframe", padding=8)
        recos_frame.grid(row=4, column=0, sticky="nsew")
        self.recommendations_text = ScrollableDetailText(recos_frame, height=7)
        self.recommendations_text.pack(fill="both", expand=True)
        self._clear_selection_state()

    def refresh_data(self) -> None:
        analyses = self.controller.list_ai_analyses()
        health = self.controller.get_ollama_health_status()
        self.model_value.set(self.controller.settings.ollama_model)
        self.ollama_badge.set(health_status_text(health.status).upper(), tone_for_status(health.status))
        self.ollama_detail.configure(text=shorten_text(health.details, 120))
        self.run_button.configure(state="disabled" if self.controller.is_task_running("ai_analysis") else "normal")

        self._rows.clear()
        self.table.clear()
        for analysis in analyses:
            item_id = self.table.tree.insert(
                "",
                "end",
                values=(format_for_ui(analysis.created_at), analysis.model, analysis.global_level, "Oui" if analysis.success else "Non"),
                tags=(analysis.global_level,),
            )
            self._rows[item_id] = analysis
        self.table.set_empty(bool(analyses), "Aucune analyse IA n'a encore ete lancee.")
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
        self.level_badge.set(analysis.global_level, analysis.global_level)
        self.values["date"].set(format_for_ui(analysis.created_at))
        self.values["model"].set(analysis.model)
        self.values["level"].set(analysis.global_level)
        self.values["success"].set("Oui" if analysis.success else "Non")
        self.summary_text.set_text(analysis.summary or "Aucun resume disponible.")
        self.threats_text.set_text("\n- ".join(["Menaces"] + (analysis.threats or ["Aucune menace detaillee."])))
        self.recommendations_text.set_text(
            "\n- ".join(["Recommandations"] + (analysis.recommendations or ["Aucune recommandation detaillee."]))
        )

    def _clear_selection_state(self) -> None:
        self.level_badge.set("N/A", "INFO")
        for value in self.values.values():
            value.set("-")
        self.summary_text.set_text("Selectionnez une analyse pour afficher le resume genere localement.")
        self.threats_text.set_text("Menaces\n- Aucune analyse selectionnee.")
        self.recommendations_text.set_text("Recommandations\n- Aucune analyse selectionnee.")
