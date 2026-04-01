from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.help_content import SCREEN_HELP
from app.ui.theme import COLORS
from app.ui.views.base import BaseView
from app.ui.widgets.common import InlineHelpPanel, LabeledValue, ScrollableDetailText, ScrollableTree, SectionHeader, StatusPill
from app.ui.widgets.risk_breakdown import RiskBreakdownWidget
from app.utils.datetime import format_for_ui
from app.utils.ui import decision_text, incident_status_text, incident_status_tone, severity_color, shorten_text


class AlertsView(BaseView):
    view_title = "Alertes"

    ACK_OPTIONS = {
        "Toutes": "",
        "Non acquittees": "no",
        "Acquittees": "yes",
    }

    INCIDENT_STATUS_OPTIONS = {
        "Nouvelle": "new",
        "En cours": "investigating",
        "Fausse alerte": "false_positive",
        "Resolue": "resolved",
    }

    DECISION_OPTIONS = {
        "Aucune": "none",
        "Whitelist": "whitelist",
        "Blacklist": "blacklist",
        "Surveiller": "watch",
        "Connu fiable": "trusted",
        "Ignorer temporairement": "ignore_temporary",
    }

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(3, weight=1)
        self._rows: dict[str, object] = {}
        self._selected_alert_key: str | None = None
        self._quick_action_busy = False

        self.header = SectionHeader(
            self,
            "Centre d'alertes",
            "Lecture rapide des alertes critiques, suivi d'incident et decisions analyste.",
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        self.help_panel = InlineHelpPanel(
            self,
            button_text=str(SCREEN_HELP["alerts"]["button"]),
            sections=list(SCREEN_HELP["alerts"]["sections"]),
        )
        self.help_panel.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        filters = ttk.LabelFrame(self, text="Filtres", style="Section.TLabelframe", padding=12)
        filters.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for column in range(4):
            filters.columnconfigure(column, weight=1 if column in {1, 3} else 0)
        self.severity_var = tk.StringVar(value="Toutes")
        self.ack_var = tk.StringVar(value="Toutes")
        ttk.Label(filters, text="Gravite").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.severity_combo = ttk.Combobox(
            filters,
            textvariable=self.severity_var,
            values=["Toutes", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
            state="readonly",
        )
        self.severity_combo.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(filters, text="Etat").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.ack_combo = ttk.Combobox(
            filters,
            textvariable=self.ack_var,
            values=list(self.ACK_OPTIONS.keys()),
            state="readonly",
        )
        self.ack_combo.grid(row=0, column=3, sticky="ew")
        ttk.Button(filters, text="Appliquer", command=self.refresh_data).grid(row=1, column=2, sticky="e", pady=(12, 0))
        ttk.Button(filters, text="Rafraichir", style="Accent.TButton", command=self.refresh_data).grid(
            row=1,
            column=3,
            sticky="e",
            pady=(12, 0),
        )
        self.severity_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_data())
        self.ack_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_data())

        list_frame = ttk.LabelFrame(self, text="Liste des alertes", style="Section.TLabelframe", padding=12)
        list_frame.grid(row=3, column=0, sticky="nsew", padx=(0, 8))
        detail_frame = ttk.LabelFrame(self, text="Detail de l'alerte", style="Section.TLabelframe", padding=12)
        detail_frame.grid(row=3, column=1, sticky="nsew", padx=(8, 0))
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(6, weight=1)

        self.table = ScrollableTree(list_frame, ("date", "severity", "title", "state", "score"), height=18)
        self.table.pack(fill="both", expand=True)
        for column, label, width in (
            ("date", "Date", 145),
            ("severity", "Gravite", 90),
            ("title", "Titre", 280),
            ("state", "Etat", 110),
            ("score", "Score", 70),
        ):
            self.table.tree.heading(column, text=label)
            self.table.tree.column(column, width=width, anchor="w")
        self.table.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_selected())
        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            self.table.tree.tag_configure(level, foreground=severity_color(level))
        self.table.tree.tag_configure("ACK", foreground=COLORS["muted"])

        top = ttk.Frame(detail_frame, style="Card.TFrame", padding=12)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="Statut", style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
        badge_row = ttk.Frame(top, style="CardInner.TFrame")
        badge_row.grid(row=0, column=1, sticky="e")
        self.severity_badge = StatusPill(badge_row, "AUCUNE", "INFO")
        self.severity_badge.pack(side="left")
        self.ack_badge = StatusPill(badge_row, "NON", "WARNING")
        self.ack_badge.pack(side="left", padx=(8, 0))
        self.case_badge = StatusPill(badge_row, "INCIDENT", "INFO")
        self.case_badge.pack(side="left", padx=(8, 0))

        metrics = ttk.Frame(detail_frame, style="Card.TFrame", padding=12)
        metrics.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        for column in range(2):
            metrics.columnconfigure(column, weight=1)
        self.values = {
            "title": LabeledValue(metrics, "Titre"),
            "date": LabeledValue(metrics, "Date"),
            "score": LabeledValue(metrics, "Score"),
            "device": LabeledValue(metrics, "Peripherique"),
            "incident_status": LabeledValue(metrics, "Incident lie"),
            "decision": LabeledValue(metrics, "Decision analyste"),
        }
        self.values["title"].grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=6)
        self.values["date"].grid(row=0, column=1, sticky="ew", pady=6)
        self.values["score"].grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=6)
        self.values["device"].grid(row=1, column=1, sticky="ew", pady=6)
        self.values["incident_status"].grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=6)
        self.values["decision"].grid(row=2, column=1, sticky="ew", pady=6)

        self.quick_action_bar = tk.Frame(
            detail_frame,
            bg=COLORS["panel_alt"],
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["panel_border"],
            padx=12,
            pady=10,
        )
        self.quick_action_bar.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.quick_action_bar.columnconfigure(5, weight=1)
        tk.Label(
            self.quick_action_bar,
            text="\u26A1 Reponse rapide :",
            bg=COLORS["panel_alt"],
            fg=COLORS["warning"],
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.quick_blacklist_button = ttk.Button(
            self.quick_action_bar,
            text="\U0001F6AB Blacklister",
            style="Danger.TButton",
            command=self._quick_blacklist,
        )
        self.quick_blacklist_button.grid(row=0, column=1, sticky="w")
        self.quick_watch_button = ttk.Button(
            self.quick_action_bar,
            text="\U0001F441 Surveiller",
            style="Accent.TButton",
            command=self._quick_watch,
        )
        self.quick_watch_button.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.quick_false_positive_button = ttk.Button(
            self.quick_action_bar,
            text="\u2713 Fausse alerte",
            style="Subtle.TButton",
            command=self._quick_false_positive,
        )
        self.quick_false_positive_button.grid(row=0, column=3, sticky="w", padx=(8, 0))
        self.quick_ai_button = ttk.Button(
            self.quick_action_bar,
            text="\U0001F916 Analyser avec l'IA",
            style="Accent.TButton",
            command=self._quick_ai_analysis,
        )
        self.quick_ai_button.grid(row=0, column=4, sticky="w", padx=(8, 0))
        self.quick_action_buttons = [
            self.quick_blacklist_button,
            self.quick_watch_button,
            self.quick_false_positive_button,
            self.quick_ai_button,
        ]
        self.quick_action_bar.grid_remove()

        workflow = ttk.LabelFrame(detail_frame, text="Workflow incident", style="Section.TLabelframe", padding=12)
        workflow.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        workflow.columnconfigure(1, weight=1)
        workflow.columnconfigure(3, weight=1)
        self.incident_status_var = tk.StringVar(value="Nouvelle")
        self.decision_var = tk.StringVar(value="Aucune")
        self.comment_var = tk.StringVar()
        self.reason_var = tk.StringVar()
        ttk.Label(workflow, text="Statut").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Combobox(
            workflow,
            textvariable=self.incident_status_var,
            values=list(self.INCIDENT_STATUS_OPTIONS.keys()),
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(workflow, text="Decision").grid(row=0, column=2, sticky="w", padx=(0, 8))
        ttk.Combobox(
            workflow,
            textvariable=self.decision_var,
            values=list(self.DECISION_OPTIONS.keys()),
            state="readonly",
        ).grid(row=0, column=3, sticky="ew")
        ttk.Label(workflow, text="Commentaire").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(12, 0))
        ttk.Entry(workflow, textvariable=self.comment_var).grid(row=1, column=1, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Label(workflow, text="Motif de cloture").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(12, 0))
        ttk.Entry(workflow, textvariable=self.reason_var).grid(row=2, column=1, columnspan=3, sticky="ew", pady=(12, 0))
        workflow_actions = ttk.Frame(workflow)
        workflow_actions.grid(row=3, column=0, columnspan=4, sticky="e", pady=(12, 0))
        self.open_case_button = ttk.Button(
            workflow_actions,
            text="Ouvrir un incident",
            style="Subtle.TButton",
            command=self._open_case,
            state="disabled",
        )
        self.open_case_button.pack(side="left")
        self.save_case_button = ttk.Button(
            workflow_actions,
            text="Enregistrer le suivi",
            style="Accent.TButton",
            command=self._save_case,
            state="disabled",
        )
        self.save_case_button.pack(side="left", padx=8)
        self.ack_button = ttk.Button(
            workflow_actions,
            text="Acquitter l'alerte",
            style="Accent.TButton",
            command=self._acknowledge,
            state="disabled",
        )
        self.ack_button.pack(side="left")

        risk_frame = ttk.LabelFrame(detail_frame, text="Decomposition du score", style="Section.TLabelframe", padding=12)
        risk_frame.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        risk_frame.columnconfigure(0, weight=1)
        self.risk_widget = RiskBreakdownWidget(risk_frame, surface="panel")
        self.risk_widget.grid(row=0, column=0, sticky="ew")

        self.investigate_button = ttk.Button(
            detail_frame,
            text="\U0001F50D Enqueter sur ce device",
            style="Subtle.TButton",
            command=self._open_investigation,
        )
        self.investigate_button.grid(row=5, column=0, sticky="e", pady=(0, 12))
        self.investigate_button.grid_remove()

        self.detail_text = ScrollableDetailText(detail_frame, height=14)
        self.detail_text.grid(row=6, column=0, sticky="nsew")
        self._clear_selection_state()

    def refresh_data(self) -> None:
        severity = "" if self.severity_var.get() == "Toutes" else self.severity_var.get()
        acknowledged = self.ACK_OPTIONS[self.ack_var.get()]
        selected_key = self._get_selected_alert_key() or self._selected_alert_key
        alerts = self.controller.list_alerts(severity, acknowledged)
        self._rows.clear()
        self.table.clear()
        item_to_restore: str | None = None
        for alert in alerts:
            tags = [alert.severity]
            if alert.acknowledged:
                tags.append("ACK")
            item_id = self.table.tree.insert(
                "",
                "end",
                values=(
                    format_for_ui(alert.created_at),
                    alert.severity,
                    shorten_text(alert.title, 48),
                    "Acquittee" if alert.acknowledged else "A traiter",
                    alert.score,
                ),
                tags=tuple(tags),
            )
            self._rows[item_id] = alert
            if self._alert_key(alert) == selected_key:
                item_to_restore = item_id
        self.table.set_empty(bool(alerts), "Aucune alerte ne correspond aux filtres actifs.")
        if item_to_restore is not None:
            self.table.tree.selection_set(item_to_restore)
            self.table.tree.focus(item_to_restore)
            self.table.tree.see(item_to_restore)
            self._show_selected()
        else:
            self._clear_selection_state()

    def _selected_alert(self):
        selection = self.table.tree.selection()
        if not selection:
            return None
        return self._rows.get(selection[0])

    def _show_selected(self) -> None:
        alert = self._selected_alert()
        if alert is None:
            self._clear_selection_state()
            return
        self._selected_alert_key = self._alert_key(alert)
        case = self.controller.get_alert_case(alert.id) if alert.id is not None else None
        assessment = self.controller.get_assessment_for_alert(alert.id) if alert.id is not None else None

        self.severity_badge.set(alert.severity, alert.severity)
        self.ack_badge.set("ACQUITTEE" if alert.acknowledged else "ACTIVE", "OK" if alert.acknowledged else "WARNING")
        if case is None:
            self.case_badge.set("A OUVRIR", "INFO")
        else:
            self.case_badge.set(incident_status_text(case.status).upper(), incident_status_tone(case.status))
        self.values["title"].set(alert.title)
        self.values["date"].set(format_for_ui(alert.created_at))
        self.values["score"].set(str(alert.score))
        self.values["device"].set(alert.device_key or "Aucun peripherique associe")
        self.values["incident_status"].set(incident_status_text(case.status) if case else "Aucun incident")
        self.values["decision"].set(decision_text(case.decision) if case else "Aucune")
        self.incident_status_var.set(self._incident_label(case.status if case else "new"))
        self.decision_var.set(self._decision_label(case.decision if case else "none"))
        self.comment_var.set(case.comment if case else alert.analyst_comment)
        self.reason_var.set(case.resolution_reason if case else alert.resolution_reason)
        self.risk_widget.update(assessment)
        self.detail_text.set_text(
            "Alerte :\n{message}\n\n"
            "Decision analyste :\n- Statut incident: {incident}\n- Decision: {decision}\n- Commentaire: {comment}\n- Resolution: {resolution}\n\n"
            "Suggestions supervisees :\n- Consulte le tableau de bord pour valider, rejeter ou reporter une suggestion.\n\n"
            "Recommandations de l'alerte :\n- {recommendations}".format(
                message=alert.message,
                incident=incident_status_text(case.status) if case else "Aucun incident ouvert",
                decision=decision_text(case.decision) if case else "Aucune",
                recommendations="\n- ".join(alert.recommendations or ["Aucune recommandation fournie."]),
                comment=(case.comment if case else alert.analyst_comment) or "Aucun commentaire",
                resolution=(case.resolution_reason if case else alert.resolution_reason) or "Non renseigne",
            )
        )
        self.open_case_button.configure(state="normal" if case is None else "disabled")
        self.save_case_button.configure(state="normal" if alert.id is not None else "disabled")
        self.ack_button.configure(state="disabled" if alert.acknowledged else "normal")
        self._sync_context_actions()

    def _clear_selection_state(self) -> None:
        self._selected_alert_key = None
        self.severity_badge.set("AUCUNE", "INFO")
        self.ack_badge.set("AUCUNE", "INFO")
        self.case_badge.set("INCIDENT", "INFO")
        for value in self.values.values():
            value.set("-")
        self.incident_status_var.set("Nouvelle")
        self.decision_var.set("Aucune")
        self.comment_var.set("")
        self.reason_var.set("")
        self.detail_text.set_text("Selectionnez une alerte pour consulter son detail, ouvrir un incident et suivre sa resolution.")
        self.risk_widget.update(None)
        self.quick_action_bar.grid_remove()
        self.investigate_button.grid_remove()
        self.open_case_button.configure(state="disabled")
        self.save_case_button.configure(state="disabled")
        self.ack_button.configure(state="disabled")
        self._set_quick_action_buttons(False, has_device=False)

    def _sync_context_actions(self) -> None:
        alert = self._selected_alert()
        if alert is None or alert.severity not in {"HIGH", "CRITICAL"}:
            self.quick_action_bar.grid_remove()
            self._set_quick_action_buttons(False, has_device=False)
        else:
            self.quick_action_bar.grid()
            self._set_quick_action_buttons(not self._quick_action_busy, has_device=bool(alert.device_key))

        if alert is not None and alert.device_key:
            self.investigate_button.grid()
            self.investigate_button.configure(state="normal")
        else:
            self.investigate_button.grid_remove()

    def _set_quick_action_buttons(self, enabled: bool, *, has_device: bool) -> None:
        normal_state = "normal" if enabled else "disabled"
        self.quick_watch_button.configure(state=normal_state)
        self.quick_false_positive_button.configure(state=normal_state)
        self.quick_ai_button.configure(state=normal_state)
        self.quick_blacklist_button.configure(state="normal" if enabled and has_device else "disabled")

    def _run_quick_action(
        self,
        action,
        *,
        success_message,
        success_level="OK",
        refresh: bool = True,
    ) -> None:
        self._quick_action_busy = True
        self._set_quick_action_buttons(False, has_device=False)
        try:
            self.run_action(
                action,
                success_message=success_message,
                success_level=success_level,
                refresh=refresh,
            )
        finally:
            self._quick_action_busy = False
            self._sync_context_actions()

    def _quick_blacklist(self) -> None:
        alert = self._selected_alert()
        if alert is None or alert.id is None or not alert.device_key:
            self.app.set_status("Aucun device associe a blacklister.", "WARNING")
            return

        def action():
            self.controller.blacklist_device(alert.device_key)
            return self.controller.update_alert_case(
                alert_id=alert.id,
                status="investigating",
                decision="blacklist",
                comment="Blacklist depuis reponse rapide",
                resolution_reason="",
            )

        self._run_quick_action(
            action,
            success_message="Device blackliste et incident ouvert.",
            success_level="WARNING",
            refresh=True,
        )

    def _quick_watch(self) -> None:
        alert = self._selected_alert()
        if alert is None or alert.id is None:
            self.app.set_status("Selectionnez une alerte a surveiller.", "WARNING")
            return

        self._run_quick_action(
            lambda: self.controller.update_alert_case(
                alert_id=alert.id,
                status="investigating",
                decision="watch",
                comment="Mise en surveillance depuis reponse rapide",
                resolution_reason="",
            ),
            success_message="Device mis en surveillance.",
            success_level="INFO",
            refresh=True,
        )

    def _quick_false_positive(self) -> None:
        alert = self._selected_alert()
        if alert is None or alert.id is None:
            self.app.set_status("Selectionnez une alerte a qualifier.", "WARNING")
            return

        self._run_quick_action(
            lambda: self.controller.update_alert_case(
                alert_id=alert.id,
                status="false_positive",
                decision="none",
                comment="",
                resolution_reason="Marque fausse alerte depuis reponse rapide",
            ),
            success_message="Alerte marquee comme fausse alerte.",
            success_level="OK",
            refresh=True,
        )

    def _quick_ai_analysis(self) -> None:
        alert = self._selected_alert()
        if alert is None:
            self.app.set_status("Selectionnez une alerte pour lancer l'analyse IA.", "WARNING")
            return
        if self.controller.get_ollama_health_status().status != "ok":
            self.app.set_status("Ollama non disponible.", "WARNING")
            return

        self._run_quick_action(
            lambda: self.controller.request_ai_analysis(),
            success_message=lambda started: "Analyse IA lancee en arriere-plan." if started else "Analyse IA deja en cours.",
            success_level=lambda started: "INFO" if started else "WARNING",
            refresh=False,
        )

    def _open_investigation(self) -> None:
        alert = self._selected_alert()
        if alert is None or not alert.device_key:
            self.app.set_status("Aucun device associe a cette alerte.", "WARNING")
            return
        self.app.show_investigation(alert.device_key)

    def _get_selected_alert_key(self) -> str | None:
        alert = self._selected_alert()
        if alert is None:
            return None
        return self._alert_key(alert)

    def _alert_key(self, alert) -> str:
        if alert.id is not None:
            return f"id:{alert.id}"
        return f"{alert.created_at}|{alert.title}|{alert.severity}"

    def _open_case(self) -> None:
        alert = self._selected_alert()
        if alert is None or alert.id is None:
            self.app.set_status("Selectionnez une alerte pour ouvrir un incident.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.ensure_alert_case(alert.id),
            success_message="Incident cree et lie a l'alerte.",
            refresh=True,
        )

    def _save_case(self) -> None:
        alert = self._selected_alert()
        if alert is None or alert.id is None:
            self.app.set_status("Selectionnez une alerte a mettre a jour.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.update_alert_case(
                alert_id=alert.id,
                status=self.INCIDENT_STATUS_OPTIONS[self.incident_status_var.get()],
                decision=self.DECISION_OPTIONS[self.decision_var.get()],
                comment=self.comment_var.get(),
                resolution_reason=self.reason_var.get(),
            ),
            success_message="Workflow incident enregistre.",
            refresh=True,
        )

    def _acknowledge(self) -> None:
        alert = self._selected_alert()
        if alert is None or alert.id is None:
            self.app.set_status("Selectionnez une alerte a acquitter.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.acknowledge_alert(alert.id),
            success_message="Alerte acquittee.",
            refresh=True,
        )

    def _incident_label(self, value: str) -> str:
        for label, raw_value in self.INCIDENT_STATUS_OPTIONS.items():
            if raw_value == value:
                return label
        return "Nouvelle"

    def _decision_label(self, value: str) -> str:
        for label, raw_value in self.DECISION_OPTIONS.items():
            if raw_value == value:
                return label
        return "Aucune"
