from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.help_content import SCREEN_HELP
from app.ui.theme import COLORS
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

    def __init__(self, parent, controller, app) -> None:
        super().__init__(parent, controller, app)
        self._rows: dict[str, object] = {}
        self._selected_alert_key: str | None = None
        self._quick_action_busy = False

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(12)
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 2)
        layout.setRowStretch(3, 1)

        self.header = SectionHeader(
            self,
            "Centre d'alertes",
            "Lecture rapide des alertes critiques, suivi d'incident et decisions analyste.",
        )
        layout.addWidget(self.header, 0, 0, 1, 2)

        self.help_panel = InlineHelpPanel(
            self,
            button_text=str(SCREEN_HELP["alerts"]["button"]),
            sections=list(SCREEN_HELP["alerts"]["sections"]),
        )
        layout.addWidget(self.help_panel, 1, 0, 1, 2)

        filters = QGroupBox("Filtres", self)
        filters_layout = QGridLayout(filters)
        filters_layout.setHorizontalSpacing(12)
        filters_layout.setVerticalSpacing(12)
        filters_layout.setColumnStretch(1, 1)
        filters_layout.setColumnStretch(3, 1)
        layout.addWidget(filters, 2, 0, 1, 2)

        filters_layout.addWidget(QLabel("Gravite", filters), 0, 0)
        self.severity_combo = QComboBox(filters)
        self.severity_combo.addItems(["Toutes", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
        filters_layout.addWidget(self.severity_combo, 0, 1)
        filters_layout.addWidget(QLabel("Etat", filters), 0, 2)
        self.ack_combo = QComboBox(filters)
        self.ack_combo.addItems(list(self.ACK_OPTIONS.keys()))
        filters_layout.addWidget(self.ack_combo, 0, 3)

        apply_button = QPushButton("Appliquer", filters)
        refresh_button = QPushButton("Rafraichir", filters)
        apply_button.clicked.connect(self.refresh_data)
        refresh_button.clicked.connect(self.refresh_data)
        filters_layout.addWidget(apply_button, 1, 2)
        filters_layout.addWidget(refresh_button, 1, 3)
        self.severity_combo.currentTextChanged.connect(lambda _text: self.refresh_data())
        self.ack_combo.currentTextChanged.connect(lambda _text: self.refresh_data())

        list_frame = QGroupBox("Liste des alertes", self)
        list_layout = QVBoxLayout(list_frame)
        detail_frame = QGroupBox("Detail de l'alerte", self)
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

        self.table = ScrollableTree(list_frame, ("date", "severity", "title", "state", "score"), height=18)
        list_layout.addWidget(self.table)
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

        top = QWidget(detail_frame)
        top.setObjectName("card")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(12, 12, 12, 12)
        top_layout.addWidget(QLabel("Statut", top), 1)
        badge_row = QWidget(top)
        badge_row_layout = QHBoxLayout(badge_row)
        badge_row_layout.setContentsMargins(0, 0, 0, 0)
        badge_row_layout.setSpacing(8)
        self.severity_badge = StatusPill(badge_row, "AUCUNE", "INFO")
        self.ack_badge = StatusPill(badge_row, "NON", "WARNING")
        self.case_badge = StatusPill(badge_row, "INCIDENT", "INFO")
        badge_row_layout.addWidget(self.severity_badge)
        badge_row_layout.addWidget(self.ack_badge)
        badge_row_layout.addWidget(self.case_badge)
        top_layout.addWidget(badge_row)
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
            "title": LabeledValue(metrics, "Titre"),
            "date": LabeledValue(metrics, "Date"),
            "score": LabeledValue(metrics, "Score"),
            "device": LabeledValue(metrics, "Peripherique"),
            "incident_status": LabeledValue(metrics, "Incident lie"),
            "decision": LabeledValue(metrics, "Decision analyste"),
        }
        self.values["title"].set("-")
        metrics_layout.addWidget(self.values["title"], 0, 0)
        metrics_layout.addWidget(self.values["date"], 0, 1)
        metrics_layout.addWidget(self.values["score"], 1, 0)
        metrics_layout.addWidget(self.values["device"], 1, 1)
        metrics_layout.addWidget(self.values["incident_status"], 2, 0)
        metrics_layout.addWidget(self.values["decision"], 2, 1)

        self.quick_action_bar = QFrame(detail_frame)
        self.quick_action_bar.setObjectName("card")
        quick_layout = QHBoxLayout(self.quick_action_bar)
        quick_layout.setContentsMargins(12, 10, 12, 10)
        quick_layout.setSpacing(8)
        quick_label = QLabel("Reponse rapide :", self.quick_action_bar)
        quick_label.setStyleSheet(f"color: {COLORS['warning']}; font-weight: 600;")
        quick_layout.addWidget(quick_label)
        self.quick_blacklist_button = QPushButton("Blacklister", self.quick_action_bar)
        self.quick_blacklist_button.setObjectName("danger")
        self.quick_watch_button = QPushButton("Surveiller", self.quick_action_bar)
        self.quick_false_positive_button = QPushButton("Fausse alerte", self.quick_action_bar)
        self.quick_false_positive_button.setObjectName("subtle")
        self.quick_ai_button = QPushButton("Analyser avec l'IA", self.quick_action_bar)
        self.quick_blacklist_button.clicked.connect(self._quick_blacklist)
        self.quick_watch_button.clicked.connect(self._quick_watch)
        self.quick_false_positive_button.clicked.connect(self._quick_false_positive)
        self.quick_ai_button.clicked.connect(self._quick_ai_analysis)
        quick_layout.addWidget(self.quick_blacklist_button)
        quick_layout.addWidget(self.quick_watch_button)
        quick_layout.addWidget(self.quick_false_positive_button)
        quick_layout.addWidget(self.quick_ai_button)
        quick_layout.addStretch(1)
        self.quick_action_buttons = [
            self.quick_blacklist_button,
            self.quick_watch_button,
            self.quick_false_positive_button,
            self.quick_ai_button,
        ]
        detail_layout.addWidget(self.quick_action_bar)
        self.quick_action_bar.hide()

        workflow = QGroupBox("Workflow incident", detail_frame)
        workflow_layout = QGridLayout(workflow)
        workflow_layout.setHorizontalSpacing(12)
        workflow_layout.setVerticalSpacing(12)
        workflow_layout.setColumnStretch(1, 1)
        workflow_layout.setColumnStretch(3, 1)
        detail_layout.addWidget(workflow)
        workflow_layout.addWidget(QLabel("Statut", workflow), 0, 0)
        self.incident_status_combo = QComboBox(workflow)
        self.incident_status_combo.addItems(list(self.INCIDENT_STATUS_OPTIONS.keys()))
        workflow_layout.addWidget(self.incident_status_combo, 0, 1)
        workflow_layout.addWidget(QLabel("Decision", workflow), 0, 2)
        self.decision_combo = QComboBox(workflow)
        self.decision_combo.addItems(list(self.DECISION_OPTIONS.keys()))
        workflow_layout.addWidget(self.decision_combo, 0, 3)
        workflow_layout.addWidget(QLabel("Commentaire", workflow), 1, 0)
        self.comment_entry = QLineEdit(workflow)
        workflow_layout.addWidget(self.comment_entry, 1, 1, 1, 3)
        workflow_layout.addWidget(QLabel("Motif de cloture", workflow), 2, 0)
        self.reason_entry = QLineEdit(workflow)
        workflow_layout.addWidget(self.reason_entry, 2, 1, 1, 3)
        workflow_actions = QWidget(workflow)
        workflow_actions_layout = QHBoxLayout(workflow_actions)
        workflow_actions_layout.setContentsMargins(0, 0, 0, 0)
        workflow_actions_layout.setSpacing(8)
        self.open_case_button = QPushButton("Ouvrir un incident", workflow_actions)
        self.open_case_button.setObjectName("subtle")
        self.save_case_button = QPushButton("Enregistrer le suivi", workflow_actions)
        self.ack_button = QPushButton("Acquitter l'alerte", workflow_actions)
        self.open_case_button.clicked.connect(self._open_case)
        self.save_case_button.clicked.connect(self._save_case)
        self.ack_button.clicked.connect(self._acknowledge)
        workflow_actions_layout.addWidget(self.open_case_button)
        workflow_actions_layout.addWidget(self.save_case_button)
        workflow_actions_layout.addWidget(self.ack_button)
        workflow_actions_layout.addStretch(1)
        workflow_layout.addWidget(workflow_actions, 3, 0, 1, 4)

        risk_frame = QGroupBox("Decomposition du score", detail_frame)
        risk_layout = QVBoxLayout(risk_frame)
        self.risk_widget = RiskBreakdownWidget(risk_frame, surface="panel")
        risk_layout.addWidget(self.risk_widget)
        detail_layout.addWidget(risk_frame)

        self.investigate_button = QPushButton("Enqueter sur ce device", detail_frame)
        self.investigate_button.setObjectName("subtle")
        self.investigate_button.clicked.connect(self._open_investigation)
        detail_layout.addWidget(self.investigate_button, 0)
        self.investigate_button.hide()

        self.detail_text = ScrollableDetailText(detail_frame, height=14)
        detail_layout.addWidget(self.detail_text, 1)
        self._clear_selection_state()

    def refresh_data(self) -> None:
        severity = "" if self.severity_combo.currentText() == "Toutes" else self.severity_combo.currentText()
        acknowledged = self.ACK_OPTIONS[self.ack_combo.currentText()]
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
        self.incident_status_combo.setCurrentText(self._incident_label(case.status if case else "new"))
        self.decision_combo.setCurrentText(self._decision_label(case.decision if case else "none"))
        self.comment_entry.setText(case.comment if case else alert.analyst_comment)
        self.reason_entry.setText(case.resolution_reason if case else alert.resolution_reason)
        self.risk_widget.set_assessment(assessment)
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
        self.open_case_button.setEnabled(case is None)
        self.save_case_button.setEnabled(alert.id is not None)
        self.ack_button.setEnabled(not alert.acknowledged)
        self._sync_context_actions()
        self.detail_page.scroll_to_top()

    def _clear_selection_state(self) -> None:
        self._selected_alert_key = None
        self.severity_badge.set("AUCUNE", "INFO")
        self.ack_badge.set("AUCUNE", "INFO")
        self.case_badge.set("INCIDENT", "INFO")
        for value in self.values.values():
            value.set("-")
        self.incident_status_combo.setCurrentText("Nouvelle")
        self.decision_combo.setCurrentText("Aucune")
        self.comment_entry.setText("")
        self.reason_entry.setText("")
        self.detail_text.set_text("Selectionnez une alerte pour consulter son detail, ouvrir un incident et suivre sa resolution.")
        self.risk_widget.set_assessment(None)
        self.quick_action_bar.hide()
        self.investigate_button.hide()
        self.open_case_button.setEnabled(False)
        self.save_case_button.setEnabled(False)
        self.ack_button.setEnabled(False)
        self._set_quick_action_buttons(False, has_device=False)

    def _sync_context_actions(self) -> None:
        alert = self._selected_alert()
        if alert is None or alert.severity not in {"HIGH", "CRITICAL"}:
            self.quick_action_bar.hide()
            self._set_quick_action_buttons(False, has_device=False)
        else:
            self.quick_action_bar.show()
            self._set_quick_action_buttons(not self._quick_action_busy, has_device=bool(alert.device_key))

        if alert is not None and alert.device_key:
            self.investigate_button.show()
            self.investigate_button.setEnabled(True)
        else:
            self.investigate_button.hide()

    def _set_quick_action_buttons(self, enabled: bool, *, has_device: bool) -> None:
        self.quick_watch_button.setEnabled(enabled)
        self.quick_false_positive_button.setEnabled(enabled)
        self.quick_ai_button.setEnabled(enabled)
        self.quick_blacklist_button.setEnabled(enabled and has_device)

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
                status=self.INCIDENT_STATUS_OPTIONS[self.incident_status_combo.currentText()],
                decision=self.DECISION_OPTIONS[self.decision_combo.currentText()],
                comment=self.comment_entry.text(),
                resolution_reason=self.reason_entry.text(),
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

    def reset_scroll_position(self) -> None:
        self.detail_page.scroll_to_top()
