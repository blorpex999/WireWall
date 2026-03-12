# Guide de demo Ydays

## Prerequis avant demo

- Poste Windows 10/11 x64
- Runtime `Python 3.11 + Tcl/Tk` valide ou build PyInstaller produit sur un tel poste
- `scripts\check_runtime.py --require-python 3.11 --require-tk` valide si vous demarrez depuis les sources
- Au moins un peripherique USB reel si vous voulez montrer la detection live
- Session admin uniquement si vous devez montrer `USBSTOR`
- Ollama local disponible uniquement si vous voulez montrer l'analyse IA
- Pour un autre poste, privilegier l'installateur ou le package portable plutot qu'un lancement source

## Ordre conseille des ecrans

1. `Dashboard`
2. `Peripheriques`
3. `Alertes`
4. `Historique`
5. `Controle USB`
6. `Analyse IA`
7. `Regles USB`
8. `Parametres`

## Scenario 5 minutes

1. Ouvrir `Dashboard` et montrer le risque global, les KPI et la sante.
2. Brancher un peripherique USB et passer sur `Peripheriques`.
3. Montrer la classification, le score, la baseline (`Nouveau`, `Connu`, `Deviation`) et le detail.
4. Ouvrir `Alertes`, creer un incident et montrer la decision analyste.
5. Revenir sur le `Dashboard` pour montrer les suggestions supervisees et la synthese du moteur local.

## Scenario 10 minutes

1. Faire le scenario 5 minutes.
2. Accepter ou refuser une suggestion supervisee depuis le `Dashboard`.
3. Ajouter une regle whitelist ou blacklist dans `Regles USB`.
4. Revenir sur `Peripheriques` ou `Historique` pour montrer l'impact sur le scoring et la memorisation.
5. Generer un export `CSV`, `JSON` ou `HTML` et mentionner le hash d'audit.
6. Si la session est admin, montrer `Controle USB` avec lecture puis blocage/deblocage `USBSTOR`.
7. Si Ollama est disponible, lancer `Analyse IA` et commenter les anomalies et recommandations.

## Points a mettre en avant

- separation claire entre mode reel et mode demo
- monitoring utilisateur honnete base sur `PyUSB/libusb1`
- policies persistantes et auditables
- baseline locale et suggestions supervisees validables
- workflow incident simple et credible pour un poste Windows unique
- blocage reel `USBSTOR` avec verification de lecture/ecriture
- IA locale sans dependance Internet
- historique et rapports exploitables pour un poste de travail

## Phrases utiles pour expliquer la valeur cyber

- "WireWall sert de demonstrateur de controle et de visibilite sur l'exposition USB d'un poste Windows."
- "Nous separons clairement ce qui est reel, ce qui depend des droits admin et ce qui depend du materiel."
- "L'application ne promet pas un driver kernel : elle assume un monitoring utilisateur robuste et documente."
- "Le mode demo est isole pour montrer des cas suspects sans falsifier les donnees reelles."

## Plans B en soutenance

### Si Ollama n'est pas disponible

- montrer l'ecran `Analyse IA`
- montrer le diagnostic d'indisponibilite
- expliquer que l'analyse est locale, optionnelle et non simulee
- montrer au besoin `Assistant IA locale` ou `Diagnostic prerequis`

### Si les droits admin ne sont pas disponibles

- montrer l'ecran `Controle USB`
- montrer l'etat non admin et le diagnostic explicite
- expliquer que le logiciel refuse toute fausse confirmation

### Si aucun vrai peripherique USB n'est branche

- utiliser `scripts\run_demo.bat`
- montrer la banniere demo et expliquer que la base est separee
- presenter alertes, historique et scoring sans pretendre a une detection materielle live

## Risques a eviter en live

- ne pas faire la demo officielle sur un host `Python 3.13` hors baseline supportee
- ne pas promettre un blocage de tout l'USB
- ne pas affirmer un temps reel noyau ou driver
- ne pas lancer une action admin sans etre sur de la session elevee
- ne pas promettre qu'un installateur installe automatiquement Ollama et un gros modele sans validation utilisateur
