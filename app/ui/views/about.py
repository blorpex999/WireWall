from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QFrame, QGridLayout, QGroupBox, QLabel, QVBoxLayout, QWidget

from app.ui.help_content import FLOW_STEPS, GLOSSARY, HONEST_LIMITS, SCREEN_HELP
from app.ui.views.base import BaseView
from app.ui.widgets.common import InlineHelpPanel, LabeledValue, ScrollablePage, ScrollableTree, SectionHeader, StatusPill
from app.version import __version__


class AboutView(BaseView):
    view_title = "A propos"

    def __init__(self, parent, controller, app) -> None:
        super().__init__(parent, controller, app)
        self._about_mode = ""
        self._flow_step_labels: list[QLabel] = []
        self._limit_labels: list[QLabel] = []

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        self.page = ScrollablePage(self)
        root_layout.addWidget(self.page)

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
            "A propos de WireWall",
            "Presentation produit, contexte Ydays et perimetre technique de la demonstration.",
        )
        self.content_layout.addWidget(self.header, 0, 0, 1, 2)

        self.help_panel = InlineHelpPanel(
            self.content,
            button_text=str(SCREEN_HELP["about"]["button"]),
            sections=list(SCREEN_HELP["about"]["sections"]),
        )
        self.content_layout.addWidget(self.help_panel, 1, 0, 1, 2)

        self.identity_frame = QFrame(self.content)
        self.identity_frame.setObjectName("card")
        identity_layout = QGridLayout(self.identity_frame)
        identity_layout.setContentsMargins(18, 18, 18, 18)
        identity_layout.setColumnStretch(0, 1)
        title = QLabel("Identite du projet", self.identity_frame)
        title.setStyleSheet("font-size: 13pt; font-weight: 600;")
        identity_layout.addWidget(title, 0, 0)
        self.mode_badge = StatusPill(self.identity_frame, "", "INFO")
        identity_layout.addWidget(self.mode_badge, 0, 1)
        self.identity_values = {
            "name": LabeledValue(self.identity_frame, "Nom"),
            "version": LabeledValue(self.identity_frame, "Version"),
            "team": LabeledValue(self.identity_frame, "Auteur / equipe"),
            "org": LabeledValue(self.identity_frame, "Organisation"),
        }
        self.content_layout.addWidget(self.identity_frame, 2, 0)
        identity_layout.addWidget(self.identity_values["name"], 1, 0, 1, 2)
        identity_layout.addWidget(self.identity_values["version"], 2, 0, 1, 2)
        identity_layout.addWidget(self.identity_values["team"], 3, 0, 1, 2)
        identity_layout.addWidget(self.identity_values["org"], 4, 0, 1, 2)

        self.mission_frame = QFrame(self.content)
        self.mission_frame.setObjectName("card")
        mission_layout = QVBoxLayout(self.mission_frame)
        mission_layout.setContentsMargins(18, 18, 18, 18)
        mission_title = QLabel("Mission", self.mission_frame)
        mission_title.setStyleSheet("font-size: 13pt; font-weight: 600;")
        mission_layout.addWidget(mission_title)
        self.mission_label = QLabel(
            "WireWall surveille les peripheriques USB Windows, journalise les evenements, applique des policies, "
            "evalue le risque et expose un controle reel USBSTOR avec analyse IA locale.",
            self.mission_frame,
        )
        self.mission_label.setObjectName("muted")
        self.mission_label.setWordWrap(True)
        mission_layout.addWidget(self.mission_label)
        flow_title = QLabel("Flux produit", self.mission_frame)
        flow_title.setStyleSheet("font-size: 13pt; font-weight: 600;")
        mission_layout.addWidget(flow_title)
        self.flow_label = QLabel(
            "Je branche un USB -> WireWall observe -> score -> alerte -> incident -> recommandation.",
            self.mission_frame,
        )
        self.flow_label.setObjectName("muted")
        self.flow_label.setWordWrap(True)
        mission_layout.addWidget(self.flow_label)
        self.content_layout.addWidget(self.mission_frame, 2, 1)

        self.stack_frame = QGroupBox("Stack technique", self.content)
        stack_layout = QVBoxLayout(self.stack_frame)
        self.stack_text = QLabel(
            "- Python 3.11+\n"
            "- PyQt6\n"
            "- PyUSB + backend libusb1\n"
            "- SQLite\n"
            "- Requests + Ollama local\n"
            "- Winreg / ctypes Windows\n"
            "- PyInstaller one-folder",
            self.stack_frame,
        )
        self.stack_text.setWordWrap(True)
        stack_layout.addWidget(self.stack_text)

        self.context_frame = QGroupBox("Contexte Ydays", self.content)
        context_layout = QVBoxLayout(self.context_frame)
        self.context_label = QLabel(
            "Demonstrateur de securite poste de travail concu pour une soutenance credible.\n\n"
            "Points forts a montrer : tableau de bord, inventaire USB, alertes, controle USBSTOR et analyse IA locale.\n\n"
            "Discours honnete : pas d'interception noyau, pas de faux succes, mode demo strictement separe du mode reel.",
            self.context_frame,
        )
        self.context_label.setWordWrap(True)
        context_layout.addWidget(self.context_label)

        self.flow_frame = QGroupBox("Fonctionnement pas a pas", self.content)
        flow_layout = QVBoxLayout(self.flow_frame)
        for title_text, detail in FLOW_STEPS:
            title_label = QLabel(title_text, self.flow_frame)
            title_label.setObjectName("muted")
            title_label.setStyleSheet("font-weight: 600;")
            detail_label = QLabel(detail, self.flow_frame)
            detail_label.setObjectName("muted")
            detail_label.setWordWrap(True)
            flow_layout.addWidget(title_label)
            flow_layout.addWidget(detail_label)
            self._flow_step_labels.append(detail_label)

        self.limits_frame = QGroupBox("Limites honnetes", self.content)
        limits_layout = QVBoxLayout(self.limits_frame)
        for item in HONEST_LIMITS:
            label = QLabel(f"- {item}", self.limits_frame)
            label.setObjectName("muted")
            label.setWordWrap(True)
            limits_layout.addWidget(label)
            self._limit_labels.append(label)

        self.glossary_frame = QGroupBox("Lexique rapide", self.content)
        glossary_layout = QVBoxLayout(self.glossary_frame)
        self.glossary = ScrollableTree(self.glossary_frame, ("term", "definition"), height=8)
        self.glossary.tree.heading("term", text="Terme")
        self.glossary.tree.heading("definition", text="Definition")
        self.glossary.tree.column("term", width=180, anchor="w")
        self.glossary.tree.column("definition", width=1050, anchor="w")
        glossary_layout.addWidget(self.glossary)

        self.on_host_resize(1450, 900)

    def refresh_data(self) -> None:
        settings = self.controller.settings
        self.identity_values["name"].set(settings.app_name)
        self.identity_values["version"].set(__version__)
        self.identity_values["team"].set(settings.author_name or "Equipe non renseignee")
        self.identity_values["org"].set(settings.organization_name or "Organisation non renseignee")
        if self.controller.demo_mode:
            self.mode_badge.set("MODE DEMO", "WARNING")
        else:
            self.mode_badge.set("MODE REEL", "INFO")
        self.glossary.clear()
        for term, definition in GLOSSARY:
            self.glossary.tree.insert("", "end", values=(term, definition))
        self.glossary.set_empty(bool(GLOSSARY), "Aucun terme a afficher.")

    def on_host_resize(self, width: int, height: int) -> None:
        mode = "stacked" if width < 1260 else "wide"
        if mode != self._about_mode:
            self._about_mode = mode
            self._apply_layout(mode)
        self._update_wraps(width)
        QTimer.singleShot(0, self.page.force_layout)

    def _apply_layout(self, mode: str) -> None:
        for frame in (
            self.identity_frame,
            self.mission_frame,
            self.stack_frame,
            self.context_frame,
            self.flow_frame,
            self.limits_frame,
            self.glossary_frame,
        ):
            self.content_layout.removeWidget(frame)

        if mode == "stacked":
            self.content_layout.addWidget(self.identity_frame, 2, 0, 1, 2)
            self.content_layout.addWidget(self.mission_frame, 3, 0, 1, 2)
            self.content_layout.addWidget(self.stack_frame, 4, 0, 1, 2)
            self.content_layout.addWidget(self.context_frame, 5, 0, 1, 2)
            self.content_layout.addWidget(self.flow_frame, 6, 0, 1, 2)
            self.content_layout.addWidget(self.limits_frame, 7, 0, 1, 2)
            self.content_layout.addWidget(self.glossary_frame, 8, 0, 1, 2)
        else:
            self.content_layout.addWidget(self.identity_frame, 2, 0)
            self.content_layout.addWidget(self.mission_frame, 2, 1)
            self.content_layout.addWidget(self.stack_frame, 3, 0)
            self.content_layout.addWidget(self.context_frame, 3, 1)
            self.content_layout.addWidget(self.flow_frame, 4, 0)
            self.content_layout.addWidget(self.limits_frame, 4, 1)
            self.content_layout.addWidget(self.glossary_frame, 5, 0, 1, 2)

    def _update_wraps(self, width: int) -> None:
        if self._about_mode == "stacked":
            primary = max(520, width - 180)
            secondary = max(520, width - 180)
            flow_width = max(600, width - 180)
        else:
            primary = 420
            secondary = 420
            flow_width = 520

        self.mission_label.setMaximumWidth(primary)
        self.flow_label.setMaximumWidth(primary)
        self.context_label.setMaximumWidth(secondary)
        for label in self._flow_step_labels:
            label.setMaximumWidth(flow_width)
        for label in self._limit_labels:
            label.setMaximumWidth(secondary)

    def reset_scroll_position(self) -> None:
        self.page.scroll_to_top()
