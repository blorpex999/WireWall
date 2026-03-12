# Checklist de validation finale

## Host de build et de demo

- [ ] Le poste cible est sous Windows 10/11 x64
- [ ] Le runtime cible est `Python 3.11`
- [ ] `python scripts\check_runtime.py --require-python 3.11 --require-tk` passe
- [ ] `python scripts\check_release_consistency.py` passe avant la release
- [ ] Le poste de soutenance n'est pas le host Python 3.13 non supporte

## Application

- [ ] L'application demarre sans erreur Python ni erreur Tkinter
- [ ] Un second lancement n'ouvre pas une deuxieme instance
- [ ] Lancement source : aucune console parasite ne reste visible par defaut
- [ ] L'UI reste reactive pendant les health checks et l'analyse IA
- [ ] Chaque vue se charge sans bouton casse ni message incoherent
- [ ] Le mode demo est visuellement distinct du mode reel
- [ ] L'icone WireWall personnalisee apparait dans la fenetre et la barre des taches

## USB

- [ ] Un branchement USB cree un evenement `connected`
- [ ] Un debranchement USB cree un evenement `disconnected`
- [ ] Un echec d'enumeration cree un evenement `scan_error` sans faux `disconnected`
- [ ] Le peripherique apparait dans `Peripheriques` avec categorie, score et niveau
- [ ] Le peripherique affiche aussi une baseline coherente (`Nouveau`, `Rare`, `Connu`, `Deviation`)
- [ ] Les policies modifient effectivement l'evaluation de risque

## Alertes et historique

- [ ] Une alerte est creee quand le seuil est depasse
- [ ] L'alerte peut etre acquittee
- [ ] Un incident peut etre ouvert depuis une alerte, commente puis resolu
- [ ] Une decision (`whitelist`, `blacklist`, `watch`, `trusted`) est memorisee proprement
- [ ] L'historique reste persistant apres redemarrage
- [ ] Les exports `CSV`, `JSON`, `HTML` sont generes dans le dossier configure
- [ ] Le rapport HTML n'injecte pas de contenu HTML brut saisi par l'utilisateur
- [ ] Le rapport exporte genere un sidecar `.sha256.txt` et un audit chaine local

## USB Control

- [ ] Le statut `USBSTOR` est lisible
- [ ] En non-admin, un diagnostic explicite est affiche
- [ ] En admin, le blocage retourne un etat relu et verifie
- [ ] En admin, le deblocage retourne un etat relu et verifie
- [ ] La demo rappelle qu'une reinsertion ou une nouvelle session peut etre necessaire

## IA locale

- [ ] Le health check Ollama reflete l'etat reel du service local
- [ ] Le lancement d'analyse IA ne bloque pas l'interface
- [ ] Une indisponibilite Ollama remonte un message explicite
- [ ] Les analyses sont historisees

## Suggestions et exploitation

- [ ] Le `Dashboard` affiche les suggestions supervisees en attente
- [ ] Une suggestion peut etre acceptee, reportee ou rejetee
- [ ] L'acceptation applique bien l'action attendue seulement apres validation utilisateur

## Packaging

- [ ] `scripts\build.bat` passe sur un poste `Python 3.11 + Tcl/Tk` valide
- [ ] `scripts\release_check.bat` passe sur le builder officiel
- [ ] `dist\WireWall\WireWall.exe` est genere
- [ ] `libusb-1.0.dll` est presente dans le bundle
- [ ] `release\WireWall-<version>-win64-portable.zip` est genere
- [ ] `release\WireWall-Setup-<version>.exe` est genere
- [ ] `release\WireWall-Setup-<version>-full.exe` est genere si la variante demo a ete construite
- [ ] Le package portable demarre sur une machine de test propre
- [ ] L'installateur se lance sur une machine de test propre
- [ ] L'installateur full se lance sur une machine de test propre
- [ ] L'application installee demarre sur une machine de test propre
- [ ] Le package affiche un message visible en cas d'echec de preflight Tk

## Installation / desinstallation

- [ ] L'installateur cree les raccourcis menu demarrer
- [ ] Les outils `Assistant IA locale` et `Diagnostic prerequis` sont presents
- [ ] `tools\OllamaSetup.exe` est present dans la variante full
- [ ] `%LOCALAPPDATA%\WireWall\` est cree au premier lancement
- [ ] La desinstallation retire les fichiers applicatifs
- [ ] La documentation signale clairement que les donnees utilisateur restent sur le poste sauf suppression manuelle

## Runtime et logs

- [ ] `%LOCALAPPDATA%\WireWall\` ou `.wirewall-runtime\WireWall\` est cree
- [ ] `logs\wirewall.log` existe
- [ ] `exports\` existe
- [ ] `config\config.json` est present et lisible

## Tests

- [ ] `python -m pytest -q tests` passe
- [ ] Les nouveaux tests de release couvrent health checks, chemins runtime, config invalide, logging et startup preflight
