from __future__ import annotations

from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from app.ui.help_content import SCREEN_HELP
from app.ui.views.base import BaseView
from app.ui.widgets.common import InlineHelpPanel, KpiCard, ScrollableDetailText, SectionHeader
from app.utils.ui import device_status_text, tone_for_status


class USBControlView(BaseView):
    view_title = "Controle USB"

    def __init__(self, parent, controller, app) -> None:
        super().__init__(parent, controller, app)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.header = SectionHeader(
            self,
            "Controle du stockage USB",
            "Lecture d'etat, actions reelles via USBSTOR et diagnostic des droits necessaires.",
        )
        layout.addWidget(self.header)

        self.help_panel = InlineHelpPanel(
            self,
            button_text=str(SCREEN_HELP["usb_control"]["button"]),
            sections=list(SCREEN_HELP["usb_control"]["sections"]),
        )
        layout.addWidget(self.help_panel)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        layout.addLayout(cards_row)
        self.card_status = KpiCard(self, "Etat USBSTOR")
        self.card_session = KpiCard(self, "Session Windows")
        self.card_mode = KpiCard(self, "Mode de fonctionnement")
        self.card_action = KpiCard(self, "Capacite d'action")
        for card in (self.card_status, self.card_session, self.card_mode, self.card_action):
            cards_row.addWidget(card, 1)

        actions = QGroupBox("Actions reelles", self)
        actions_layout = QHBoxLayout(actions)
        self.block_button = QPushButton("Bloquer le stockage USB", actions)
        self.block_button.setObjectName("danger")
        self.unblock_button = QPushButton("Debloquer le stockage USB", actions)
        self.refresh_button = QPushButton("Relire le diagnostic", actions)
        self.refresh_button.setObjectName("subtle")
        self.relaunch_button = QPushButton("Relancer en admin", actions)
        self.relaunch_button.setObjectName("subtle")
        self.block_button.clicked.connect(self._block)
        self.unblock_button.clicked.connect(self._unblock)
        self.refresh_button.clicked.connect(self.refresh_data)
        self.relaunch_button.clicked.connect(self._relaunch)
        actions_layout.addWidget(self.block_button)
        actions_layout.addWidget(self.unblock_button)
        actions_layout.addWidget(self.refresh_button)
        actions_layout.addWidget(self.relaunch_button)
        actions_layout.addStretch(1)
        layout.addWidget(actions)

        lockdown = QGroupBox("Verrouillage total des ports USB", self)
        lockdown_layout = QVBoxLayout(lockdown)
        self.lockdown_note = QLabel(
            "Option avancee: applique les policies Windows USB, bloque les services USB et desactive les peripheriques deja branches. "
            "Prevoir un clavier/touchpad non USB ou un acces distant avant activation.",
            lockdown,
        )
        self.lockdown_note.setObjectName("muted")
        self.lockdown_note.setWordWrap(True)
        lockdown_layout.addWidget(self.lockdown_note)
        lockdown_actions = QHBoxLayout()
        self.block_all_button = QPushButton("Bloquer tous les ports USB", lockdown)
        self.block_all_button.setObjectName("danger")
        self.restore_all_button = QPushButton("Restaurer tous les ports USB", lockdown)
        self.restore_all_button.setObjectName("subtle")
        self.block_all_button.clicked.connect(self._block_all)
        self.restore_all_button.clicked.connect(self._restore_all)
        lockdown_actions.addWidget(self.block_all_button)
        lockdown_actions.addWidget(self.restore_all_button)
        lockdown_actions.addStretch(1)
        lockdown_layout.addLayout(lockdown_actions)
        layout.addWidget(lockdown)

        diagnostics = QGroupBox("Diagnostic detaille", self)
        diagnostics_layout = QVBoxLayout(diagnostics)
        self.note_label = QLabel(
            "Les actions de blocage/deblocage ne concernent que USBSTOR et peuvent necessiter une reinsertion du peripherique.",
            diagnostics,
        )
        self.note_label.setObjectName("muted")
        self.note_label.setWordWrap(True)
        diagnostics_layout.addWidget(self.note_label)
        self.detail_text = ScrollableDetailText(diagnostics, height=20)
        diagnostics_layout.addWidget(self.detail_text, 1)
        layout.addWidget(diagnostics, 1)

    def refresh_data(self) -> None:
        status = self.controller.get_usb_control_status()
        full_status = self.controller.get_full_usb_lockdown_status()
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
            "Scenario simule actif: aucune action USBSTOR reelle." if demo_mode else "Actions reelles disponibles selon les droits.",
            tone="WARNING" if demo_mode else "INFO",
            pill_text="SIMULE" if demo_mode else "LIVE",
        )
        if demo_mode:
            self.card_action.set("Suspendue", "Les boutons USBSTOR sont desactives en mode demo.", tone="WARNING", pill_text="DEMO")
        elif is_admin:
            self.card_action.set("Disponible", "Le registre USBSTOR peut etre modifie et relu.", tone="OK", pill_text="WRITE")
        else:
            self.card_action.set("Lecture seule", "Le diagnostic reste disponible sans elevation.", tone="WARNING", pill_text="READ")
        self.block_button.setEnabled(not demo_mode)
        self.unblock_button.setEnabled(not demo_mode)
        self.block_all_button.setEnabled(not demo_mode)
        self.restore_all_button.setEnabled(not demo_mode)

        self.detail_text.set_text(
            "Lecture courante :\n"
            "- Message : {message}\n"
            "- Statut : {status_value}\n"
            "- Details : {details}\n\n"
            "Verrouillage total USB :\n"
            "- Etat : {full_status}\n"
            "- Message : {full_message}\n"
            "- Details : {full_details}\n\n"
            "Ce que USBSTOR bloque :\n"
            "- Le stockage USB de type cle, disque externe ou support de masse.\n\n"
            "Ce que USBSTOR ne bloque pas :\n"
            "- Les souris, claviers, receivers HID, hubs ou la plupart des peripheriques non stockage.\n\n"
            "Ce que le verrouillage total peut bloquer :\n"
            "- Les policies Windows Device Installation, les controleurs/hubs USB et les peripheriques deja presents via PnP.\n"
            "- Le stockage amovible via Deny_All, donc disque externe ou cle USB doivent devenir illisibles.\n\n"
            "Pourquoi admin est requis :\n"
            "- WireWall doit modifier une cle registre Windows protegee puis relire le resultat.\n\n"
            "Pourquoi une reinsertion peut etre necessaire :\n"
            "- Un support deja monte peut rester present tant qu'il n'est pas rebranche ou que la session n'est pas renouvelee.\n\n"
            "Diagnostic brut : {diagnostic}".format(
                message=status.message,
                status_value=status.status,
                details=status.details,
                full_status=full_status.status,
                full_message=full_status.message,
                full_details=full_status.details,
                diagnostic=diagnostics,
            )
        )

    def _confirm(self, message: str) -> bool:
        return QMessageBox.question(self, "Confirmation", message) == QMessageBox.StandardButton.Yes

    def _block(self) -> None:
        if self.controller.demo_mode:
            self.app.set_status("Mode demo actif: aucune action USBSTOR reelle n'est appliquee.", "WARNING")
            return
        diagnostics = self.controller.usb_diagnostics()
        if not diagnostics.get("is_admin"):
            self.app.set_status("Cette action requiert une session administrateur.", "WARNING")
            self.refresh_data()
            return
        if not self._confirm("Bloquer reellement le stockage USB via USBSTOR ?"):
            return
        self.run_action(
            self.controller.block_usb_storage,
            success_message=lambda result: result.message,
            success_level=lambda result: "OK" if result.success else "ERROR",
            refresh=True,
        )

    def _unblock(self) -> None:
        if self.controller.demo_mode:
            self.app.set_status("Mode demo actif: aucune action USBSTOR reelle n'est appliquee.", "WARNING")
            return
        diagnostics = self.controller.usb_diagnostics()
        if not diagnostics.get("is_admin"):
            self.app.set_status("Cette action requiert une session administrateur.", "WARNING")
            self.refresh_data()
            return
        if not self._confirm("Debloquer reellement le stockage USB via USBSTOR ?"):
            return
        self.run_action(
            self.controller.unblock_usb_storage,
            success_message=lambda result: result.message,
            success_level=lambda result: "OK" if result.success else "ERROR",
            refresh=True,
        )

    def _block_all(self) -> None:
        if self.controller.demo_mode:
            self.app.set_status("Mode demo actif: aucun verrouillage USB total reel n'est applique.", "WARNING")
            return
        diagnostics = self.controller.usb_diagnostics()
        if not diagnostics.get("is_admin"):
            self.app.set_status("Cette action requiert une session administrateur.", "WARNING")
            self.refresh_data()
            return
        message = (
            "Bloquer TOUS les ports USB Windows ?\n\n"
            "Cette action applique les policies Windows officielles, bloque les services USB et desactive aussi les peripheriques deja branches.\n"
            "Elle peut couper souris, clavier, hubs, disque USB, adaptateurs et certains appareils internes immediatement.\n"
            "Un redemarrage peut etre necessaire pour que Windows applique le blocage partout.\n"
            "La restauration peut etre difficile sans clavier/touchpad non USB ou acces distant.\n\n"
            "Continuer seulement si tu as un moyen de reprendre la main."
        )
        if not self._confirm(message):
            return
        self.run_action(
            self.controller.block_all_usb_ports,
            success_message=lambda result: result.message,
            success_level=lambda result: "WARNING" if result.success else "ERROR",
            refresh=True,
        )

    def _restore_all(self) -> None:
        if self.controller.demo_mode:
            self.app.set_status("Mode demo actif: aucune restauration USB totale reelle n'est appliquee.", "WARNING")
            return
        diagnostics = self.controller.usb_diagnostics()
        if not diagnostics.get("is_admin"):
            self.app.set_status("Cette action requiert une session administrateur.", "WARNING")
            self.refresh_data()
            return
        message = (
            "Restaurer les ports USB Windows ?\n\n"
            "WireWall va retirer les policies de blocage, remettre les services USB, reactiver les peripheriques PnP et demander a Windows "
            "de relancer la pile USB avec les options Microsoft qui autorisent un redemarrage si Windows l'exige.\n\n"
            "Si un controleur USB est bloque par le pilote, Windows peut redemarrer ou demander un redemarrage pour terminer."
        )
        if not self._confirm(message):
            return
        self.run_action(
            self.controller.restore_all_usb_ports,
            success_message=lambda result: (
                f"{result.message} Redemarrage Windows recommande."
                if result.details.get("reboot_requested")
                else result.message
            ),
            success_level=lambda result: "WARNING" if result.details.get("reboot_requested") else ("OK" if result.success else "ERROR"),
            refresh=True,
        )

    def _relaunch(self) -> None:
        relaunched = self.run_action(self.controller.relaunch_admin)
        if relaunched:
            self.app.set_status("Tentative de relance administrateur envoyee.", "INFO")
        elif relaunched is False:
            self.app.set_status("Relance administrateur impossible.", "ERROR")
