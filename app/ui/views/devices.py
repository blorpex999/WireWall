from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
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
from app.utils.ui import (
    category_text,
    decision_text,
    device_status_text,
    severity_color,
    shorten_text,
    trust_state_text,
    trust_state_tone,
)


class DevicesView(BaseView):
    view_title = "Peripheriques"

    CATEGORY_OPTIONS = {
        "Toutes les categories": "",
        "Stockage": "storage",
        "HID": "hid",
        "Hub": "hub",
        "Imagerie": "imaging",
        "Communication": "communication",
        "Specifique constructeur": "vendor_specific",
        "Inconnu": "unknown",
    }
    STATUS_OPTIONS = {
        "Tous les statuts": "",
        "Connecte": "connected",
        "Deconnecte": "disconnected",
    }

    def __init__(self, parent, controller, app) -> None:
        super().__init__(parent, controller, app)
        self._rows: dict[str, object] = {}
        self._selected_device_key: str | None = None

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(12)
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 2)
        layout.setRowStretch(3, 1)

        self.header = SectionHeader(
            self,
            "Peripheriques USB",
            "Inventaire actif, contexte de confiance et actions de policy sur les equipements observes.",
            "MODE DEMO" if self.controller.demo_mode else "MODE REEL",
            "WARNING" if self.controller.demo_mode else "INFO",
        )
        layout.addWidget(self.header, 0, 0, 1, 2)

        self.help_panel = InlineHelpPanel(
            self,
            button_text=str(SCREEN_HELP["devices"]["button"]),
            sections=list(SCREEN_HELP["devices"]["sections"]),
        )
        layout.addWidget(self.help_panel, 1, 0, 1, 2)

        filters = QGroupBox("Filtres et actions", self)
        filters_layout = QGridLayout(filters)
        filters_layout.setHorizontalSpacing(12)
        filters_layout.setVerticalSpacing(12)
        filters_layout.setColumnStretch(1, 1)
        filters_layout.setColumnStretch(3, 1)
        filters_layout.setColumnStretch(5, 1)
        layout.addWidget(filters, 2, 0, 1, 2)

        filters_layout.addWidget(QLabel("Recherche", filters), 0, 0)
        self.search_entry = QLineEdit(filters)
        filters_layout.addWidget(self.search_entry, 0, 1)

        filters_layout.addWidget(QLabel("Categorie", filters), 0, 2)
        self.category_combo = QComboBox(filters)
        self.category_combo.addItems(list(self.CATEGORY_OPTIONS.keys()))
        filters_layout.addWidget(self.category_combo, 0, 3)

        filters_layout.addWidget(QLabel("Statut", filters), 0, 4)
        self.status_combo = QComboBox(filters)
        self.status_combo.addItems(list(self.STATUS_OPTIONS.keys()))
        filters_layout.addWidget(self.status_combo, 0, 5)

        apply_button = QPushButton("Appliquer les filtres", filters)
        apply_button.clicked.connect(self.refresh_data)
        filters_layout.addWidget(apply_button, 1, 4)

        refresh_button = QPushButton("Rafraichir l'USB", filters)
        refresh_button.clicked.connect(self._refresh_monitor)
        filters_layout.addWidget(refresh_button, 1, 5)

        self.search_entry.textChanged.connect(lambda _text: self.schedule_refresh(250))
        self.search_entry.returnPressed.connect(self.refresh_data)
        self.category_combo.currentTextChanged.connect(lambda _text: self.refresh_data())
        self.status_combo.currentTextChanged.connect(lambda _text: self.refresh_data())

        tree_frame = QGroupBox("Inventaire des peripheriques", self)
        tree_layout = QVBoxLayout(tree_frame)
        detail_frame = QGroupBox("Fiche peripherique", self)
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_page = ScrollablePage(detail_frame)
        detail_layout.addWidget(self.detail_page)
        detail_body = QWidget(self.detail_page.body)
        self.detail_page.body_layout.addWidget(detail_body)
        detail_layout = QVBoxLayout(detail_body)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(12)
        layout.addWidget(tree_frame, 3, 0)
        layout.addWidget(detail_frame, 3, 1)

        self.table = ScrollableTree(tree_frame, ("vidpid", "name", "category", "trust", "status", "score"), height=18)
        tree_layout.addWidget(self.table)
        for column, label, width in (
            ("vidpid", "VID:PID", 100),
            ("name", "Peripherique", 280),
            ("category", "Categorie", 120),
            ("trust", "Habitude", 115),
            ("status", "Etat", 105),
            ("score", "Score", 70),
        ):
            self.table.tree.heading(column, text=label)
            self.table.tree.column(column, width=width, anchor="w")
        self.table.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_selected())
        for tone in ("LOW", "MEDIUM", "HIGH", "CRITICAL", "connected", "disconnected", "KNOWN", "NEW", "RARE", "DEVIATION"):
            self.table.tree.tag_configure(tone, foreground=severity_color(tone))

        detail_top = QWidget(detail_frame)
        detail_top.setObjectName("card")
        detail_top_layout = QHBoxLayout(detail_top)
        detail_top_layout.setContentsMargins(12, 12, 12, 12)
        detail_top_layout.addWidget(QLabel("Selection actuelle", detail_top), 1)
        badge_row = QWidget(detail_top)
        badge_row_layout = QHBoxLayout(badge_row)
        badge_row_layout.setContentsMargins(0, 0, 0, 0)
        badge_row_layout.setSpacing(8)
        self.status_badge = StatusPill(badge_row, "INCONNU", "INFO")
        self.trust_badge = StatusPill(badge_row, "N/A", "INFO")
        self.risk_badge = StatusPill(badge_row, "LOW", "LOW")
        badge_row_layout.addWidget(self.status_badge)
        badge_row_layout.addWidget(self.trust_badge)
        badge_row_layout.addWidget(self.risk_badge)
        detail_top_layout.addWidget(badge_row, 0)
        detail_layout.addWidget(detail_top)

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
            "name": LabeledValue(metrics, "Nom"),
            "vidpid": LabeledValue(metrics, "VID:PID"),
            "serial": LabeledValue(metrics, "Numero de serie"),
            "category": LabeledValue(metrics, "Categorie"),
            "confidence": LabeledValue(metrics, "Confiance"),
            "backend": LabeledValue(metrics, "Backend"),
            "status": LabeledValue(metrics, "Etat"),
            "bus": LabeledValue(metrics, "Bus / Adresse"),
            "trust": LabeledValue(metrics, "Baseline locale"),
            "seen": LabeledValue(metrics, "Occurrences"),
            "decision": LabeledValue(metrics, "Derniere decision"),
            "variation": LabeledValue(metrics, "Variation"),
            "source": LabeledValue(metrics, "Identification"),
            "score": LabeledValue(metrics, "Risque"),
        }
        positions = [
            ("name", 0, 0),
            ("vidpid", 0, 1),
            ("serial", 1, 0),
            ("category", 1, 1),
            ("confidence", 2, 0),
            ("backend", 2, 1),
            ("status", 3, 0),
            ("bus", 3, 1),
            ("trust", 4, 0),
            ("seen", 4, 1),
            ("decision", 5, 0),
            ("variation", 5, 1),
            ("source", 6, 0),
            ("score", 6, 1),
        ]
        for key, row, column in positions:
            metrics_layout.addWidget(self.values[key], row, column)

        actions = QWidget(detail_frame)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        self.whitelist_button = QPushButton("Ajouter a la liste blanche", actions)
        self.blacklist_button = QPushButton("Ajouter a la liste noire", actions)
        self.blacklist_button.setObjectName("danger")
        self.whitelist_button.setEnabled(False)
        self.blacklist_button.setEnabled(False)
        self.whitelist_button.clicked.connect(self._whitelist)
        self.blacklist_button.clicked.connect(self._blacklist)
        actions_layout.addWidget(self.whitelist_button)
        actions_layout.addWidget(self.blacklist_button)
        actions_layout.addStretch(1)
        detail_layout.addWidget(actions)

        self.detail_text = ScrollableDetailText(detail_frame, height=16)
        detail_layout.addWidget(self.detail_text, 1)
        self._clear_selection_state()

    def refresh_data(self) -> None:
        selected_key = self._get_selected_device_key() or self._selected_device_key
        devices = self.controller.list_devices(
            search=self.search_entry.text().strip(),
            category=self.CATEGORY_OPTIONS[self.category_combo.currentText()],
            status=self.STATUS_OPTIONS[self.status_combo.currentText()],
        )
        self._rows.clear()
        self.table.clear()
        item_to_restore: str | None = None
        for device in devices:
            item_id = self.table.tree.insert(
                "",
                "end",
                values=(
                    device.vid_pid,
                    shorten_text(device.display_name, 42),
                    category_text(device.category),
                    trust_state_text(device.trust_state),
                    device_status_text(device.status),
                    device.risk_score,
                ),
                tags=(device.risk_level, device.status, device.trust_state),
            )
            self._rows[item_id] = device
            if device.device_key == selected_key:
                item_to_restore = item_id
        self.table.set_empty(bool(devices), "Aucun peripherique ne correspond aux filtres actifs.")
        if item_to_restore is not None:
            self.table.tree.selection_set(item_to_restore)
            self.table.tree.focus(item_to_restore)
            self.table.tree.see(item_to_restore)
            self._show_selected()
        else:
            self._clear_selection_state()

    def _selected_device(self):
        selection = self.table.tree.selection()
        if not selection:
            return None
        return self._rows.get(selection[0])

    def _show_selected(self) -> None:
        device = self._selected_device()
        if device is None:
            self._clear_selection_state()
            return
        self._selected_device_key = device.device_key
        self.status_badge.set(device_status_text(device.status), device.status)
        self.trust_badge.set(trust_state_text(device.trust_state).upper(), trust_state_tone(device.trust_state))
        self.risk_badge.set(device.risk_level, device.risk_level)
        self.values["name"].set(device.display_name)
        self.values["vidpid"].set(device.vid_pid)
        self.values["serial"].set(device.serial_number or "Non disponible")
        self.values["category"].set(category_text(device.category))
        self.values["confidence"].set(f"{device.confidence:.0%}")
        self.values["backend"].set(device.source_backend)
        self.values["status"].set(device_status_text(device.status))
        self.values["bus"].set(f"{device.bus or '-'} / {device.address or '-'}")
        self.values["trust"].set(trust_state_text(device.trust_state))
        self.values["seen"].set(str(device.seen_count))
        self.values["decision"].set(decision_text(device.last_decision))
        self.values["variation"].set(device.recent_variation or "stable")
        self.values["source"].set(device.identification_source)
        self.values["score"].set(f"{device.risk_level} ({device.risk_score})")
        history = (
            self.controller.get_device_history(device.device_key, limit=8)
            if hasattr(self.controller, "get_device_history")
            else []
        )
        history_lines = [
            f"- {format_for_ui(event.occurred_at)} | {event.event_type} | {event.severity} | {event.summary}"
            for event in history
        ] or ["- Aucun historique recent disponible."]
        self.detail_text.set_text(
            "Donnees observees :\n"
            "- Premiere observation : {first_seen}\n"
            "- Derniere observation : {last_seen}\n"
            "- Classe USB : {usb_class}\n"
            "- Bus / Adresse : {bus_address}\n"
            "- Source backend : {backend}\n"
            "- Metadata brutes : {metadata}\n\n"
            "Interpretation WireWall :\n"
            "- Source d'identification : {source}\n"
            "- Baseline : {trust}\n"
            "- Score de risque : {score}\n"
            "- Derniere decision : {decision}\n"
            "- Plages d'usage : {usual_hours}\n\n"
            "Historique recent :\n{history}".format(
                first_seen=format_for_ui(device.first_seen),
                last_seen=format_for_ui(device.last_seen),
                usb_class=device.usb_class if device.usb_class is not None else "-",
                bus_address=f"{device.bus or '-'} / {device.address or '-'}",
                backend=device.source_backend,
                source=device.identification_source,
                trust=trust_state_text(device.trust_state),
                score=f"{device.risk_level} ({device.risk_score})",
                decision=decision_text(device.last_decision),
                usual_hours=device.usual_hours or {},
                metadata=device.metadata,
                history="\n".join(history_lines),
            )
        )
        self.detail_page.scroll_to_top()
        self.whitelist_button.setEnabled(True)
        self.blacklist_button.setEnabled(True)

    def _clear_selection_state(self) -> None:
        self._selected_device_key = None
        self.status_badge.set("AUCUNE SELECTION", "INFO")
        self.trust_badge.set("N/A", "INFO")
        self.risk_badge.set("N/A", "INFO")
        for value in self.values.values():
            value.set("-")
        self.detail_text.set_text("Selectionnez un peripherique pour afficher sa fiche technique, sa baseline et son historique.")
        self.whitelist_button.setEnabled(False)
        self.blacklist_button.setEnabled(False)

    def _get_selected_device_key(self) -> str | None:
        device = self._selected_device()
        if device is None:
            return None
        return device.device_key

    def _whitelist(self) -> None:
        device = self._selected_device()
        if device is None:
            self.app.set_status("Selectionnez un peripherique a autoriser.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.whitelist_device(device.device_key),
            success_message="Peripherique ajoute a la liste blanche.",
        )

    def _blacklist(self) -> None:
        device = self._selected_device()
        if device is None:
            self.app.set_status("Selectionnez un peripherique a bloquer.", "WARNING")
            return
        self.run_action(
            lambda: self.controller.blacklist_device(device.device_key),
            success_message="Peripherique ajoute a la liste noire.",
            success_level="HIGH",
        )

    def _refresh_monitor(self) -> None:
        self.controller.refresh_monitor()
        self.app.set_status("Rafraichissement USB demande.", "INFO")

    def reset_scroll_position(self) -> None:
        self.detail_page.scroll_to_top()
