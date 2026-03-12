from __future__ import annotations

from tkinter import ttk

from app.ui.help_content import FLOW_STEPS, GLOSSARY, HONEST_LIMITS, SCREEN_HELP
from app.ui.views.base import BaseView
from app.ui.widgets.common import InlineHelpPanel, LabeledValue, ScrollableTree, SectionHeader, StatusPill
from app.version import __version__


class AboutView(BaseView):
    view_title = "A propos"

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(5, weight=1)

        self.header = SectionHeader(
            self,
            "A propos de WireWall",
            "Presentation produit, contexte Ydays et perimetre technique de la demonstration.",
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        self.help_panel = InlineHelpPanel(
            self,
            button_text=str(SCREEN_HELP["about"]["button"]),
            sections=list(SCREEN_HELP["about"]["sections"]),
        )
        self.help_panel.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        identity = ttk.Frame(self, style="Card.TFrame", padding=18)
        identity.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        identity.columnconfigure(0, weight=1)
        ttk.Label(identity, text="Identite du projet", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        badge_box = ttk.Frame(identity, style="CardInner.TFrame")
        badge_box.grid(row=0, column=1, sticky="e")
        self.mode_badge = StatusPill(badge_box, "", "INFO")
        self.mode_badge.pack(side="left")
        self.identity_values = {
            "name": LabeledValue(identity, "Nom"),
            "version": LabeledValue(identity, "Version"),
            "team": LabeledValue(identity, "Auteur / equipe"),
            "org": LabeledValue(identity, "Organisation"),
        }
        self.identity_values["name"].grid(row=1, column=0, sticky="ew", pady=(14, 0))
        self.identity_values["version"].grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.identity_values["team"].grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.identity_values["org"].grid(row=4, column=0, sticky="ew", pady=(10, 0))

        mission = ttk.Frame(self, style="Card.TFrame", padding=18)
        mission.grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        mission.columnconfigure(0, weight=1)
        ttk.Label(mission, text="Mission", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            mission,
            text=(
                "WireWall surveille les peripheriques USB Windows, journalise les evenements, applique des policies, "
                "evalue le risque et expose un controle reel USBSTOR avec analyse IA locale."
            ),
            style="Muted.TLabel",
            wraplength=420,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Label(mission, text="Flux produit", style="CardTitle.TLabel").grid(row=2, column=0, sticky="w", pady=(18, 0))
        ttk.Label(
            mission,
            text="Je branche un USB -> WireWall observe -> score -> alerte -> incident -> recommandation.",
            style="Muted.TLabel",
            wraplength=420,
            justify="left",
        ).grid(row=3, column=0, sticky="w", pady=(10, 0))

        stack = ttk.LabelFrame(self, text="Stack technique", style="Section.TLabelframe", padding=16)
        stack.grid(row=3, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        ttk.Label(
            stack,
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
        ).pack(anchor="w")

        context = ttk.LabelFrame(self, text="Contexte Ydays", style="Section.TLabelframe", padding=16)
        context.grid(row=3, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        ttk.Label(
            context,
            text=(
                "Demonstrateur de securite poste de travail concu pour une soutenance credible.\n\n"
                "Points forts a montrer : tableau de bord, inventaire USB, alertes, controle USBSTOR et analyse IA locale.\n\n"
                "Discours honnete : pas d'interception noyau, pas de faux succes, mode demo strictement separe du mode reel."
            ),
            justify="left",
            wraplength=420,
        ).pack(anchor="w")

        flow = ttk.LabelFrame(self, text="Fonctionnement pas a pas", style="Section.TLabelframe", padding=16)
        flow.grid(row=4, column=0, sticky="nsew", padx=(0, 8))
        for index, (title, detail) in enumerate(FLOW_STEPS):
            ttk.Label(flow, text=title, style="ValueTitle.TLabel").grid(row=index * 2, column=0, sticky="w")
            ttk.Label(flow, text=detail, style="Muted.TLabel", wraplength=520, justify="left").grid(
                row=index * 2 + 1,
                column=0,
                sticky="w",
                pady=(2, 10 if index < len(FLOW_STEPS) - 1 else 0),
            )

        limits = ttk.LabelFrame(self, text="Limites honnetes", style="Section.TLabelframe", padding=16)
        limits.grid(row=4, column=1, sticky="nsew", padx=(8, 0))
        for index, item in enumerate(HONEST_LIMITS):
            ttk.Label(limits, text=f"- {item}", style="Muted.TLabel", wraplength=420, justify="left").grid(
                row=index,
                column=0,
                sticky="w",
                pady=(0, 8 if index < len(HONEST_LIMITS) - 1 else 0),
            )

        glossary = ttk.LabelFrame(self, text="Lexique rapide", style="Section.TLabelframe", padding=12)
        glossary.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        glossary.rowconfigure(0, weight=1)
        glossary.columnconfigure(0, weight=1)
        self.glossary = ScrollableTree(glossary, ("term", "definition"), height=8)
        self.glossary.grid(row=0, column=0, sticky="nsew")
        self.glossary.tree.heading("term", text="Terme")
        self.glossary.tree.heading("definition", text="Definition")
        self.glossary.tree.column("term", width=180, anchor="w")
        self.glossary.tree.column("definition", width=1050, anchor="w")

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
