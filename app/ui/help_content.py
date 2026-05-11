from __future__ import annotations

SCREEN_HELP: dict[str, dict[str, object]] = {
    "dashboard": {
        "button": "Comprendre le tableau de bord",
        "sections": [
            ("Ce que montre l'ecran", "Vue synthese du poste: risque, incidents, suggestions et sante des composants."),
            ("Observe reellement", "Detection USB, alertes, etats techniques, exports et statut Windows relus localement."),
            ("Deduit ou calcule", "Score global, baseline, incidents ouverts et suggestions supervisees viennent des regles WireWall."),
            ("A dire en soutenance", "WireWall centralise les signaux USB d'un poste et aide la decision sans agir seul."),
        ],
    },
    "devices": {
        "button": "Comprendre les peripheriques",
        "sections": [
            ("Ce que montre l'ecran", "Inventaire USB avec details techniques, baseline locale et decisions deja prises."),
            ("Observe reellement", "VID:PID, serial si disponible, bus/adresse, statut courant et evenements persistants."),
            ("Deduit ou calcule", "Categorie, baseline, score de risque et variation recente sont interpretes par WireWall."),
            ("A dire en soutenance", "On distingue toujours la donnee brute USB de l'interpretation cyber faite par l'app."),
        ],
    },
    "alerts": {
        "button": "Comprendre les alertes",
        "sections": [
            ("Ce que montre l'ecran", "Alertes persistantes, incident lie, decision analyste et commentaire de suivi."),
            ("Observe reellement", "Une alerte est generee a partir d'un evenement, d'un score et d'un contexte device."),
            ("Deduit ou calcule", "L'incident, la decision et la suggestion sont des couches de pilotage au-dessus de l'alerte."),
            ("A dire en soutenance", "Une alerte signale un risque; un incident formalise le traitement humain de ce risque."),
        ],
    },
    "usb_control": {
        "button": "Comprendre le controle USB",
        "sections": [
            ("Ce que montre l'ecran", "Etat USBSTOR, verrouillage total USB, niveau de droits et capacite reelle d'agir sur Windows."),
            ("Observe reellement", "WireWall lit/ecrit USBSTOR, des services USB Windows, et desactive les peripheriques USB presents via PnP."),
            ("Deduit ou calcule", "La capacite d'action depend du mode reel/demo, des droits admin et du retour registre."),
            ("A dire en soutenance", "USBSTOR bloque le stockage; le verrouillage total agit plus bas et peut aussi couper souris/clavier USB."),
        ],
    },
    "ai_analysis": {
        "button": "Comprendre l'analyse IA",
        "sections": [
            ("Ce que montre l'ecran", "Analyses locales generees via Ollama a partir du contexte collecte par WireWall."),
            ("Observe reellement", "Modele configure, etat Ollama, historique d'analyses et reponse brute du service local."),
            ("Deduit ou calcule", "Le resume, les anomalies et recommandations sont proposes par l'IA, jamais appliquees seules."),
            ("A dire en soutenance", "L'IA reste locale, optionnelle et assiste l'analyste sans remplacer les verifications humaines."),
        ],
    },
    "about": {
        "button": "Comprendre WireWall",
        "sections": [
            ("Ce que montre l'ecran", "Mission du produit, flux fonctionnel, limites assumees et vocabulaire a connaitre."),
            ("Observe reellement", "WireWall s'appuie sur des lectures locales Windows, PyUSB/libusb, SQLite et Ollama local."),
            ("Deduit ou calcule", "Le risque, les incidents, la baseline et les suggestions viennent des regles et de la memoire locale."),
            ("A dire en soutenance", "Le logiciel est un demonstrateur honnete de supervision USB poste client, pas un driver noyau."),
        ],
    },
}

GLOSSARY: list[tuple[str, str]] = [
    ("USB", "Bus de connexion de peripheriques. WireWall observe ce qui est visible depuis l'espace utilisateur."),
    ("VID/PID", "Identifiants constructeur et produit. Ils servent a reconnaitre une famille de peripheriques."),
    ("HID", "Human Interface Device: souris, clavier, receiver ou autre peripherique d'entree."),
    ("Hub", "Concentrateur USB qui redistribue plusieurs ports derriere un meme point de connexion."),
    ("Storage", "Categorie stockage USB. C'est cette famille que USBSTOR peut bloquer ou debloquer."),
    ("Serial", "Numero de serie USB si le materiel et le pilote l'exposent. Il aide a distinguer deux devices identiques."),
    ("Bus / Address", "Coordonnees de branchement a un instant donne. Elles peuvent changer au rebranchement."),
    ("PyUSB / libusb", "Couche de lecture USB en espace utilisateur. Ce n'est pas un driver noyau Windows."),
    ("Snapshot utilisateur", "Photo de l'etat USB a un instant T, comparee ensuite pour detecter les changements."),
    ("USBSTOR", "Service Windows qui controle le stockage USB. Il ne bloque pas les claviers, souris ou hubs."),
    ("Verrouillage total USB", "Action admin avancee sur les services controleur/hub USB Windows et les peripheriques PnP deja presents."),
    ("Whitelist / Blacklist", "Listes de confiance ou de refus basees sur VID:PID ou numero de serie."),
    ("Baseline", "Memoire locale d'usage: nouveau, rare, connu ou en deviation par rapport aux habitudes observees."),
    ("Incident", "Traitement analyste d'une alerte: statut, decision, commentaire et resolution."),
    ("Suggestion supervisee", "Action proposee par WireWall ou l'IA, jamais appliquee sans validation utilisateur."),
]

FLOW_STEPS: list[tuple[str, str]] = [
    ("1. Observation", "Un branchement, debranchement ou changement d'etat USB est detecte par snapshots PyUSB/libusb."),
    ("2. Enrichissement", "WireWall complete les informations disponibles: categorie, identifiants, contexte et historique local."),
    ("3. Evaluation", "Le moteur de regles calcule un score de risque, un niveau et des raisons explicites."),
    ("4. Action", "Si besoin, une alerte apparait, un incident est ouvert et des suggestions restent a valider."),
    ("5. Restitution", "Le tableau de bord, les exports et l'IA locale presentent l'etat du poste sans faux succes."),
]

HONEST_LIMITS: list[str] = [
    "Pas d'interception noyau: WireWall reste un outil de supervision utilisateur documente.",
    "USBSTOR agit sur le stockage USB uniquement; le verrouillage total USB est plus risque et peut couper les peripheriques d'entree immediatement.",
    "L'IA depend d'Ollama local et peut etre absente sans bloquer le reste de l'application.",
    "Certaines metadonnees USB peuvent manquer selon le materiel, le pilote ou les droits.",
]
