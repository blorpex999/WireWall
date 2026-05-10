from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.ui.views.base import BaseView
from app.ui.widgets.common import ScrollablePage, SectionHeader


class SettingsView(BaseView):
    view_title = "Parametres"

    def __init__(self, parent, controller, app) -> None:
        super().__init__(parent, controller, app)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.page = ScrollablePage(self)
        layout.addWidget(self.page)

        self.content = QWidget(self.page.body)
        self.page.body_layout.addWidget(self.content)
        self.content_layout = QGridLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setHorizontalSpacing(16)
        self.content_layout.setVerticalSpacing(12)
        self.content_layout.setColumnStretch(0, 1)
        self.content_layout.setColumnStretch(1, 1)

        self.header = SectionHeader(
            self.content,
            "Parametres",
            "Reglage du monitoring, de la retention, du profil de securite, des suggestions et de l'integration Ollama.",
        )
        self.content_layout.addWidget(self.header, 0, 0, 1, 2)

        self.fields: dict[str, QLineEdit | QComboBox] = {}
        self.checks = {
            "demo_mode": QCheckBox("Activer le mode demo USB simule", self.content),
            "autostart_enabled": QCheckBox("Activer le demarrage avec Windows", self.content),
            "desktop_notifications_enabled": QCheckBox(
                "Notifications locales des alertes HIGH / CRITICAL",
                self.content,
            ),
        }

        monitoring = QGroupBox("Monitoring", self.content)
        monitoring_layout = QGridLayout(monitoring)
        monitoring_layout.setColumnStretch(1, 1)
        self._add_entry_field(monitoring_layout, 0, "Frequence de scan (s)", "scan_interval_seconds")
        self._add_combo_field(monitoring_layout, 1, "Profil de securite", "security_profile", ["Normal", "Strict", "Presentation"])
        monitoring_layout.addWidget(self.checks["demo_mode"], 2, 0, 1, 2)
        monitoring_layout.addWidget(self.checks["autostart_enabled"], 3, 0, 1, 2)
        self.content_layout.addWidget(monitoring, 1, 0)

        audit = QGroupBox("Audit, alertes et suggestions", self.content)
        audit_layout = QGridLayout(audit)
        audit_layout.setColumnStretch(1, 1)
        self._add_entry_field(audit_layout, 0, "Retention historique (jours)", "history_retention_days")
        self._add_combo_field(audit_layout, 1, "Niveau de logs", "log_level", ["DEBUG", "INFO", "WARNING", "ERROR"])
        self._add_combo_field(audit_layout, 2, "Mode recommandations", "recommendation_mode", ["conservative", "balanced", "proactive"])
        audit_layout.addWidget(self.checks["desktop_notifications_enabled"], 3, 0, 1, 2)
        self.content_layout.addWidget(audit, 1, 1)

        ollama = QGroupBox("IA locale Ollama", self.content)
        ollama_layout = QGridLayout(ollama)
        ollama_layout.setColumnStretch(1, 1)
        self._add_entry_field(ollama_layout, 0, "URL locale", "ollama_base_url")
        self._add_entry_field(ollama_layout, 1, "Modele", "ollama_model")
        self._add_entry_field(ollama_layout, 2, "Timeout (s)", "ollama_timeout_seconds")
        self.content_layout.addWidget(ollama, 2, 0)

        paths = QGroupBox("Chemins", self.content)
        paths_layout = QGridLayout(paths)
        paths_layout.setColumnStretch(1, 1)
        self._add_entry_field(paths_layout, 0, "Dossier des exports", "export_directory")
        paths_layout.addWidget(QLabel("Base SQLite", paths), 1, 0)
        self.db_path_label = QLabel("", paths)
        self.db_path_label.setObjectName("muted")
        self.db_path_label.setWordWrap(True)
        paths_layout.addWidget(self.db_path_label, 1, 1)
        self.content_layout.addWidget(paths, 2, 1)

        footer = QWidget(self.content)
        footer.setObjectName("card")
        footer_layout = QGridLayout(footer)
        footer_layout.setContentsMargins(16, 16, 16, 16)
        footer_layout.setColumnStretch(0, 1)
        note = QLabel(
            "Les changements prennent effet au prochain cycle de monitoring, au prochain rapport et au prochain appel Ollama.",
            footer,
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        footer_layout.addWidget(note, 0, 0)
        save_button = QPushButton("Enregistrer les parametres", footer)
        save_button.clicked.connect(self._save)
        footer_layout.addWidget(save_button, 0, 1)
        self.content_layout.addWidget(footer, 3, 0, 1, 2)

    def on_host_resize(self, width: int, height: int) -> None:
        QTimer.singleShot(0, self.page.force_layout)

    def reset_scroll_position(self) -> None:
        self.page.scroll_to_top()

    def refresh_data(self) -> None:
        settings = self.controller.settings
        for field_name, widget in self.fields.items():
            value = str(getattr(settings, field_name))
            if isinstance(widget, QComboBox):
                widget.setCurrentText(value)
            else:
                widget.setText(value)
        for field_name, widget in self.checks.items():
            if field_name == "demo_mode":
                widget.setChecked(self.controller.demo_mode)
            else:
                widget.setChecked(bool(getattr(settings, field_name)))
        self.db_path_label.setText(str(self.controller.get_database_path()))
        self.page.force_layout()

    def _save(self) -> None:
        values: dict[str, object] = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QComboBox):
                values[key] = widget.currentText()
            else:
                values[key] = widget.text()
        for key, widget in self.checks.items():
            values[key] = widget.isChecked()
        result = self.run_action(
            lambda: self.controller.save_settings(values),
            success_message=self._success_message,
            refresh=True,
        )
        if result is not None:
            if result.mode != self.controller.settings.mode:
                self.app.restart_for_mode_switch(result.mode)
            else:
                self.app.refresh_mode_state(refresh_views=True)

    def _success_message(self, settings) -> str:
        notice = self.controller.consume_settings_notice()
        base_message = f"Parametres enregistres. Profil actif : {settings.security_profile}"
        if notice is None:
            return base_message
        return f"{base_message} | {notice[0]}"

    def _add_entry_field(self, layout: QGridLayout, row: int, label: str, field_name: str) -> None:
        layout.addWidget(QLabel(label), row, 0)
        entry = QLineEdit()
        layout.addWidget(entry, row, 1)
        self.fields[field_name] = entry

    def _add_combo_field(self, layout: QGridLayout, row: int, label: str, field_name: str, values: list[str]) -> None:
        layout.addWidget(QLabel(label), row, 0)
        combo = QComboBox()
        combo.addItems(values)
        layout.addWidget(combo, row, 1)
        self.fields[field_name] = combo
