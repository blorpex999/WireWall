from __future__ import annotations

from tkinter import ttk

from app.ui.help_content import FLOW_STEPS, GLOSSARY, HONEST_LIMITS, SCREEN_HELP
from app.ui.views.base import BaseView
from app.ui.widgets.common import InlineHelpPanel, LabeledValue, ScrollablePage, ScrollableTree, SectionHeader, StatusPill
from app.version import __version__


class AboutView(BaseView):
    view_title = "A propos"

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._about_mode = ""
        self._wrap_labels: list[ttk.Label] = []
        self.page = ScrollablePage(self)
        self.page.grid(row=0, column=0, sticky="nsew")
        self.content = self.page.body
        self.content.columnconfigure(0, weight=1)
        self.content.columnconfigure(1, weight=1)
        self.content.rowconfigure(5, weight=1)

        self.header = SectionHeader(
            self.content,
            "A propos de WireWall",
            "Presentation produit, contexte Ydays et perimetre technique de la demonstration.",
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        self.help_panel = InlineHelpPanel(
            self.content,
            button_text=str(SCREEN_HELP["about"]["button"]),
            sections=list(SCREEN_HELP["about"]["sections"]),
        )
        self.help_panel.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        self.identity_frame = ttk.Frame(self.content, style="Card.TFrame", padding=18)
        self.identity_frame.columnconfigure(0, weight=1)
        ttk.Label(self.identity_frame, text="Identite du projet", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        badge_box = ttk.Frame(self.identity_frame, style="CardInner.TFrame")
        badge_box.grid(row=0, column=1, sticky="e")
        self.mode_badge = StatusPill(badge_box, "", "INFO")
        self.mode_badge.pack(side="left")
        self.identity_values = {
            "name": LabeledValue(self.identity_frame, "Nom"),
            "version": LabeledValue(self.identity_frame, "Version"),
            "team": LabeledValue(self.identity_frame, "Auteur / equipe"),
            "org": LabeledValue(self.identity_frame, "Organisation"),
        }
        self.identity_values["name"].grid(row=1, column=0, sticky="ew", pady=(14, 0))
        self.identity_values["version"].grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.identity_values["team"].grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.identity_values["org"].grid(row=4, column=0, sticky="ew", pady=(10, 0))

        self.mission_frame = ttk.Frame(self.content, style="Card.TFrame", padding=18)
        self.mission_frame.columnconfigure(0, weight=1)
        ttk.Label(self.mission_frame, text="Mission", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.mission_label = ttk.Label(
            self.mission_frame,
            text=(
                "WireWall surveille les peripheriques USB Windows, journalise les evenements, applique des policies, "
                "evalue le risque et expose un controle reel USBSTOR avec analyse IA locale."
            ),
            style="CardMuted.TLabel",
            wraplength=420,
            justify="left",
        )
        self.mission_label.grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Label(self.mission_frame, text="Flux produit", style="CardTitle.TLabel").grid(row=2, column=0, sticky="w", pady=(18, 0))
        self.flow_label = ttk.Label(
            self.mission_frame,
            text="Je branche un USB -> WireWall observe -> score -> alerte -> incident -> recommandation.",
            style="CardMuted.TLabel",
            wraplength=420,
            justify="left",
        )
        self.flow_label.grid(row=3, column=0, sticky="w", pady=(10, 0))
        self._wrap_labels.extend([self.mission_label, self.flow_label])

        self.stack_frame = ttk.LabelFrame(self.content, text="Stack technique", style="Section.TLabelframe", padding=16)
        self.stack_text = ttk.Label(
            self.stack_frame,
            text=(
                "- Python 3.11+\n"
                "- Tkinter / ttk\n"
                "- PyUSB + backend libusb1\n"
                "- SQLite\n"
                "- Requests + Ollama local\n"
                "- Winreg / ctypes Windows\n"
                "- PyInstaller one-folder"
            ),
            justify="left",
        )
        self.stack_text.pack(anchor="w")

        self.context_frame = ttk.LabelFrame(self.content, text="Contexte Ydays", style="Section.TLabelframe", padding=16)
        self.context_label = ttk.Label(
            self.context_frame,
            text=(
                "Demonstrateur de securite poste de travail concu pour une soutenance credible.\n\n"
                "Points forts a montrer : tableau de bord, inventaire USB, alertes, controle USBSTOR et analyse IA locale.\n\n"
                "Discours honnete : pas d'interception noyau, pas de faux succes, mode demo strictement separe du mode reel."
            ),
            justify="left",
            wraplength=420,
        )
        self.context_label.pack(anchor="w")
        self._wrap_labels.append(self.context_label)

        self.flow_frame = ttk.LabelFrame(self.content, text="Fonctionnement pas a pas", style="Section.TLabelframe", padding=16)
        self.flow_step_labels: list[ttk.Label] = []
        for index, (title, detail) in enumerate(FLOW_STEPS):
            ttk.Label(self.flow_frame, text=title, style="ValueTitle.TLabel").grid(row=index * 2, column=0, sticky="w")
            detail_label = ttk.Label(self.flow_frame, text=detail, style="Muted.TLabel", wraplength=520, justify="left")
            detail_label.grid(
                row=index * 2 + 1,
                column=0,
                sticky="w",
                pady=(2, 10 if index < len(FLOW_STEPS) - 1 else 0),
            )
            self.flow_step_labels.append(detail_label)
        self._wrap_labels.extend(self.flow_step_labels)

        self.limits_frame = ttk.LabelFrame(self.content, text="Limites honnetes", style="Section.TLabelframe", padding=16)
        self.limit_labels: list[ttk.Label] = []
        for index, item in enumerate(HONEST_LIMITS):
            label = ttk.Label(self.limits_frame, text=f"- {item}", style="Muted.TLabel", wraplength=420, justify="left")
            label.grid(
                row=index,
                column=0,
                sticky="w",
                pady=(0, 8 if index < len(HONEST_LIMITS) - 1 else 0),
            )
            self.limit_labels.append(label)
        self._wrap_labels.extend(self.limit_labels)

        self.glossary_frame = ttk.LabelFrame(self.content, text="Lexique rapide", style="Section.TLabelframe", padding=12)
        self.glossary_frame.rowconfigure(0, weight=1)
        self.glossary_frame.columnconfigure(0, weight=1)
        self.glossary = ScrollableTree(self.glossary_frame, ("term", "definition"), height=8)
        self.glossary.grid(row=0, column=0, sticky="nsew")
        self.glossary.tree.heading("term", text="Terme")
        self.glossary.tree.heading("definition", text="Definition")
        self.glossary.tree.column("term", width=180, anchor="w")
        self.glossary.tree.column("definition", width=1050, anchor="w")
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
        self.after_idle(self.page._on_body_configure, None)

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
            frame.grid_forget()

        for row in range(9):
            self.content.rowconfigure(row, weight=0)

        if mode == "stacked":
            self.identity_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
            self.mission_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
            self.stack_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
            self.context_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
            self.flow_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
            self.limits_frame.grid(row=7, column=0, columnspan=2, sticky="nsew")
            self.glossary_frame.grid(row=8, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
            self.content.rowconfigure(8, weight=1)
        else:
            self.identity_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
            self.mission_frame.grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
            self.stack_frame.grid(row=3, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
            self.context_frame.grid(row=3, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
            self.flow_frame.grid(row=4, column=0, sticky="nsew", padx=(0, 8))
            self.limits_frame.grid(row=4, column=1, sticky="nsew", padx=(8, 0))
            self.glossary_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
            self.content.rowconfigure(5, weight=1)

    def _update_wraps(self, width: int) -> None:
        if self._about_mode == "stacked":
            primary = max(520, width - 180)
            secondary = max(520, width - 180)
            flow_width = max(600, width - 180)
        else:
            primary = 420
            secondary = 420
            flow_width = 520

        self.mission_label.configure(wraplength=primary)
        self.flow_label.configure(wraplength=primary)
        self.context_label.configure(wraplength=secondary)
        for label in self.flow_step_labels:
            label.configure(wraplength=flow_width)
        for label in self.limit_labels:
            label.configure(wraplength=secondary)

    def reset_scroll_position(self) -> None:
        self.page.scroll_to_top()
