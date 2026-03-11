from __future__ import annotations

from tkinter import ttk

from app.ui.views.base import BaseView
from app.ui.widgets.common import LabeledValue, SectionHeader, StatusPill
from app.version import __version__


class AboutView(BaseView):
    view_title = "A propos"

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.header = SectionHeader(
            self,
            "A propos de WireWall",
            "Presentation produit, contexte Ydays et perimetre technique de la demonstration.",
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        identity = ttk.Frame(self, style="Card.TFrame", padding=18)
        identity.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
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
        mission.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
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

        stack = ttk.LabelFrame(self, text="Stack technique", style="Section.TLabelframe", padding=16)
        stack.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
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
        context.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
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
