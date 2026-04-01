from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.views.base import BaseView
from app.ui.widgets.common import ScrollableTree, SectionHeader, StatusPill
from app.utils.ui import match_type_text, policy_type_text, shorten_text


class PoliciesView(BaseView):
    view_title = "Regles USB"

    def __init__(self, parent, controller, app) -> None:
        super().__init__(parent, controller, app)
        self.tables: dict[str, ScrollableTree] = {}
        self.row_maps: dict[str, dict[str, object]] = {"whitelist": {}, "blacklist": {}}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.header = SectionHeader(
            self,
            "Regles USB",
            "Gestion separee des listes blanche et noire, import/export et regles cibles.",
        )
        layout.addWidget(self.header)

        controls = QGroupBox("Recherche et echanges", self)
        controls_layout = QGridLayout(controls)
        controls_layout.setColumnStretch(1, 1)
        controls_layout.addWidget(QLabel("Recherche", controls), 0, 0)
        self.query_entry = QLineEdit(controls)
        controls_layout.addWidget(self.query_entry, 0, 1)
        apply_button = QPushButton("Appliquer", controls)
        import_button = QPushButton("Importer", controls)
        export_button = QPushButton("Exporter", controls)
        apply_button.clicked.connect(self.refresh_data)
        import_button.clicked.connect(self._import)
        export_button.clicked.connect(self._export)
        controls_layout.addWidget(apply_button, 0, 2)
        controls_layout.addWidget(import_button, 0, 3)
        controls_layout.addWidget(export_button, 0, 4)
        self.query_entry.textChanged.connect(lambda _text: self.schedule_refresh(250))
        self.query_entry.returnPressed.connect(self.refresh_data)
        layout.addWidget(controls)

        self.notebook = QTabWidget(self)
        self.tabs: dict[str, QWidget] = {}
        layout.addWidget(self.notebook, 1)
        for policy_type in ("whitelist", "blacklist"):
            tab = QWidget(self.notebook)
            tab_layout = QVBoxLayout(tab)
            self.notebook.addTab(tab, policy_type_text(policy_type))
            self.tabs[policy_type] = tab
            self._build_policy_tab(tab_layout, policy_type)
        self.notebook.currentChanged.connect(lambda _index: self._sync_form_target())

        form = QGroupBox("Ajouter une regle", self)
        form_layout = QGridLayout(form)
        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(2, 1)
        form_layout.setColumnStretch(3, 1)
        form_layout.setColumnStretch(4, 1)
        form_layout.addWidget(QLabel("Cible", form), 0, 0)
        self.target_badge = StatusPill(form, "", "OK")
        form_layout.addWidget(self.target_badge, 0, 1)
        form_layout.addWidget(QLabel("Type de match", form), 1, 0)
        self.new_match = QComboBox(form)
        self.new_match.addItems(["VID:PID", "Numero de serie"])
        form_layout.addWidget(self.new_match, 1, 1)
        form_layout.addWidget(QLabel("Valeur", form), 1, 2)
        self.new_value = QLineEdit(form)
        form_layout.addWidget(self.new_value, 1, 3)
        form_layout.addWidget(QLabel("Label", form), 2, 0)
        self.new_label = QLineEdit(form)
        form_layout.addWidget(self.new_label, 2, 1, 1, 2)
        form_layout.addWidget(QLabel("Notes", form), 2, 3)
        self.new_notes = QLineEdit(form)
        form_layout.addWidget(self.new_notes, 2, 4)
        self.add_button = QPushButton("", form)
        self.add_button.clicked.connect(self._add_policy)
        form_layout.addWidget(self.add_button, 3, 4)
        layout.addWidget(form)
        self._sync_form_target()

    def refresh_data(self) -> None:
        query = self.query_entry.text().strip()
        for policy_type in ("whitelist", "blacklist"):
            entries = self.controller.list_policies(policy_type, query)
            self.row_maps[policy_type].clear()
            table = self.tables[policy_type]
            table.clear()
            for entry in entries:
                item_id = table.tree.insert(
                    "",
                    "end",
                    values=(match_type_text(entry.match_type), entry.value, shorten_text(entry.label, 36), shorten_text(entry.notes, 52)),
                )
                self.row_maps[policy_type][item_id] = entry
            table.set_empty(bool(entries), f"Aucune regle {policy_type_text(policy_type).lower()} pour ce filtre.")
            self.notebook.setTabText(self.notebook.indexOf(self.tabs[policy_type]), f"{policy_type_text(policy_type)} ({len(entries)})")

    def _build_policy_tab(self, tab_layout: QVBoxLayout, policy_type: str) -> None:
        top = QWidget()
        top.setObjectName("card")
        top_layout = QGridLayout(top)
        top_layout.setContentsMargins(12, 12, 12, 12)
        top_layout.setColumnStretch(0, 1)
        label = QLabel(f"{policy_type_text(policy_type)} active", top)
        label.setObjectName("muted")
        top_layout.addWidget(label, 0, 0)
        tone = "OK" if policy_type == "whitelist" else "CRITICAL"
        badge = StatusPill(top, policy_type_text(policy_type).upper(), tone)
        top_layout.addWidget(badge, 0, 1)
        delete_button = QPushButton("Supprimer la selection", top)
        delete_button.setObjectName("subtle")
        delete_button.clicked.connect(lambda: self._delete_policy(policy_type))
        top_layout.addWidget(delete_button, 1, 1)
        tab_layout.addWidget(top)

        table = ScrollableTree(None, ("match", "value", "label", "notes"), height=12)
        for column, label, width in (
            ("match", "Match", 150),
            ("value", "Valeur", 220),
            ("label", "Label", 240),
            ("notes", "Notes", 340),
        ):
            table.tree.heading(column, text=label)
            table.tree.column(column, width=width, anchor="w")
        tab_layout.addWidget(table, 1)
        self.tables[policy_type] = table

    def _current_policy_type(self) -> str:
        current_widget = self.notebook.currentWidget()
        for policy_type, frame in self.tabs.items():
            if frame is current_widget:
                return policy_type
        return "whitelist"

    def _sync_form_target(self) -> None:
        policy_type = self._current_policy_type()
        tone = "OK" if policy_type == "whitelist" else "CRITICAL"
        self.target_badge.set(policy_type_text(policy_type).upper(), tone)
        self.add_button.setText(f"Ajouter a la {policy_type_text(policy_type).lower()}")

    def _add_policy(self) -> None:
        policy_type = self._current_policy_type()
        match_type = "vid_pid" if self.new_match.currentText() == "VID:PID" else "serial"
        self.run_action(
            lambda: self.controller.add_policy(
                policy_type,
                match_type,
                self.new_value.text().strip(),
                self.new_label.text().strip(),
                self.new_notes.text().strip(),
            ),
            success_message=f"Regle ajoutee a la {policy_type_text(policy_type).lower()}.",
            refresh=True,
        )

    def _delete_policy(self, policy_type: str) -> None:
        table = self.tables[policy_type].tree
        selection = table.selection()
        if not selection:
            self.app.set_status("Selectionnez une regle a supprimer.", "WARNING")
            return
        entry = self.row_maps[policy_type].get(selection[0])
        if entry is None or entry.id is None:
            return
        if QMessageBox.question(self, "Confirmation", f"Supprimer cette regle de {policy_type_text(policy_type).lower()} ?") != QMessageBox.StandardButton.Yes:
            return
        self.run_action(
            lambda: self.controller.remove_policy(entry.id),
            success_message="Regle supprimee.",
            refresh=True,
        )

    def _import(self) -> None:
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Importer des regles",
            "",
            "Regles USB (*.json *.csv);;JSON (*.json);;CSV (*.csv)",
        )
        if not path:
            return
        self.run_action(
            lambda: self.controller.import_policies(path),
            success_message=lambda count: f"{count} regle(s) importee(s) depuis {path}.",
            refresh=True,
        )

    def _export(self) -> None:
        default_path = Path(self.controller.settings.export_directory) / "wirewall_policies.json"
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exporter les regles",
            str(default_path),
            "JSON (*.json);;CSV (*.csv)",
        )
        if not path:
            return
        self.run_action(
            lambda: self.controller.export_policies(path),
            success_message=lambda target: f"Regles exportees : {target}",
        )
