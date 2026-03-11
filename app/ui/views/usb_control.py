from __future__ import annotations

from tkinter import messagebox, ttk

from app.ui.views.base import BaseView
from app.ui.widgets.common import KpiCard, ScrollableDetailText, SectionHeader
from app.utils.ui import device_status_text, tone_for_status


class USBControlView(BaseView):
    view_title = "Controle USB"

    def __init__(self, master, controller, app) -> None:
        super().__init__(master, controller, app)
        for column in range(4):
            self.columnconfigure(column, weight=1)
        self.rowconfigure(3, weight=1)

        self.header = SectionHeader(
            self,
            "Controle du stockage USB",
            "Lecture d'etat, actions reelles via USBSTOR et diagnostic des droits necessaires.",
        )
        self.header.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 16))

        self.card_status = KpiCard(self, "Etat USBSTOR")
        self.card_session = KpiCard(self, "Session Windows")
        self.card_mode = KpiCard(self, "Mode de fonctionnement")
        self.card_action = KpiCard(self, "Capacite d'action")
        self.card_status.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        self.card_session.grid(row=1, column=1, sticky="nsew", padx=8, pady=(0, 12))
        self.card_mode.grid(row=1, column=2, sticky="nsew", padx=8, pady=(0, 12))
        self.card_action.grid(row=1, column=3, sticky="nsew", padx=(8, 0), pady=(0, 12))

        actions = ttk.LabelFrame(self, text="Actions reelles", style="Section.TLabelframe", padding=12)
        actions.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(0, 12))
        ttk.Button(actions, text="Bloquer le stockage USB", style="Danger.TButton", command=self._block).pack(side="left")
        ttk.Button(actions, text="Debloquer le stockage USB", style="Accent.TButton", command=self._unblock).pack(side="left", padx=8)
        ttk.Button(actions, text="Relire le diagnostic", style="Subtle.TButton", command=self.refresh_data).pack(side="left", padx=8)
        ttk.Button(actions, text="Relancer en admin", style="Subtle.TButton", command=self._relaunch).pack(side="left", padx=8)

        diagnostics = ttk.LabelFrame(self, text="Diagnostic detaille", style="Section.TLabelframe", padding=12)
        diagnostics.grid(row=3, column=0, columnspan=4, sticky="nsew")
        diagnostics.columnconfigure(0, weight=1)
        diagnostics.rowconfigure(1, weight=1)
        self.note_label = ttk.Label(
            diagnostics,
            text="Les actions de blocage/deblocage ne concernent que USBSTOR et peuvent necessiter une reinsertion du peripherique.",
            style="Muted.TLabel",
            wraplength=1120,
            justify="left",
        )
        self.note_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.detail_text = ScrollableDetailText(diagnostics, height=20)
        self.detail_text.grid(row=1, column=0, sticky="nsew")

    def refresh_data(self) -> None:
        status = self.controller.get_usb_control_status()
        diagnostics = self.controller.usb_diagnostics()
        is_admin = bool(diagnostics.get("is_admin"))
        demo_mode = self.controller.demo_mode

        self.card_status.set(
            device_status_text(status.status),
            status.message,
            tone=tone_for_status(status.status),
            pill_text=device_status_text(status.status).upper(),
        )
        self.card_session.set(
            "Administrateur" if is_admin else "Standard",
            "Privileges eleves actifs." if is_admin else "Privileges insuffisants pour ecrire USBSTOR.",
            tone="OK" if is_admin else "WARNING",
            pill_text="ADMIN" if is_admin else "LIMITEE",
        )
        self.card_mode.set(
            "DEMO" if demo_mode else "REEL",
            "Aucune action reelle autorisee en demo." if demo_mode else "Actions reelles disponibles selon les droits.",
            tone="WARNING" if demo_mode else "INFO",
            pill_text="ISOLE" if demo_mode else "LIVE",
        )
        if demo_mode:
            self.card_action.set("Desactivee", "Le mode demo ne doit pas agir sur le poste.", tone="WARNING", pill_text="SAFE")
        elif is_admin:
            self.card_action.set("Disponible", "Le registre USBSTOR peut etre modifie et relu.", tone="OK", pill_text="WRITE")
        else:
            self.card_action.set("Lecture seule", "Le diagnostic reste disponible sans elevation.", tone="WARNING", pill_text="READ")

        self.detail_text.set_text(
            "Message : {message}\n"
            "Statut : {status_value}\n"
            "Details : {details}\n\n"
            "Diagnostic : {diagnostic}\n\n"
            "Limites reelles :\n"
            "- Le blocage agit uniquement sur le stockage USB.\n"
            "- Un support deja monte peut necessiter une reinsertion.\n"
            "- Certaines situations peuvent demander une nouvelle session Windows.".format(
                message=status.message,
                status_value=status.status,
                details=status.details,
                diagnostic=diagnostics,
            )
        )

    def _block(self) -> None:
        diagnostics = self.controller.usb_diagnostics()
        if self.controller.demo_mode:
            self.app.set_status("Action desactivee en mode demo pour eviter toute confusion avec le mode reel.", "WARNING")
            return
        if not diagnostics.get("is_admin"):
            self.app.set_status("Cette action requiert une session administrateur.", "WARNING")
            self.refresh_data()
            return
        if not messagebox.askyesno("Confirmation", "Bloquer reellement le stockage USB via USBSTOR ?"):
            return
        self.run_action(
            self.controller.block_usb_storage,
            success_message=lambda result: result.message,
            success_level=lambda result: "OK" if result.success else "ERROR",
            refresh=True,
        )

    def _unblock(self) -> None:
        diagnostics = self.controller.usb_diagnostics()
        if self.controller.demo_mode:
            self.app.set_status("Action desactivee en mode demo pour eviter toute confusion avec le mode reel.", "WARNING")
            return
        if not diagnostics.get("is_admin"):
            self.app.set_status("Cette action requiert une session administrateur.", "WARNING")
            self.refresh_data()
            return
        if not messagebox.askyesno("Confirmation", "Debloquer reellement le stockage USB via USBSTOR ?"):
            return
        self.run_action(
            self.controller.unblock_usb_storage,
            success_message=lambda result: result.message,
            success_level=lambda result: "OK" if result.success else "ERROR",
            refresh=True,
        )

    def _relaunch(self) -> None:
        relaunched = self.run_action(self.controller.relaunch_admin)
        if relaunched:
            self.app.set_status("Tentative de relance administrateur envoyee.", "INFO")
        elif relaunched is False:
            self.app.set_status("Relance administrateur impossible.", "ERROR")
