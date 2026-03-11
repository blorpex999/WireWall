# Checklist de validation finale

## Host de build et de demo

- [ ] Le poste cible est sous Windows 10/11 x64
- [ ] Le runtime cible est `Python 3.11`
- [ ] `python scripts\check_runtime.py --require-python 3.11 --require-tk` passe
- [ ] Le poste de soutenance n'est pas le host Python 3.13 non supporte

## Application

- [ ] L'application demarre sans erreur Python ni erreur Tkinter
- [ ] L'UI reste reactive pendant les health checks et l'analyse IA
- [ ] Chaque vue se charge sans bouton casse ni message incoherent
- [ ] Le mode demo est visuellement distinct du mode reel

## USB

- [ ] Un branchement USB cree un evenement `connected`
- [ ] Un debranchement USB cree un evenement `disconnected`
- [ ] Un echec d'enumeration cree un evenement `scan_error` sans faux `disconnected`
- [ ] Le peripherique apparait dans `Peripheriques` avec categorie, score et niveau
- [ ] Les policies modifient effectivement l'evaluation de risque

## Alertes et historique

- [ ] Une alerte est creee quand le seuil est depasse
- [ ] L'alerte peut etre acquittee
- [ ] L'historique reste persistant apres redemarrage
- [ ] Les exports `CSV`, `JSON`, `HTML` sont generes dans le dossier configure
- [ ] Le rapport HTML n'injecte pas de contenu HTML brut saisi par l'utilisateur

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

## Packaging

- [ ] `scripts\build.bat` passe sur un poste `Python 3.11 + Tcl/Tk` valide
- [ ] `scripts\release_check.bat` passe sur le builder officiel
- [ ] `dist\WireWall\WireWall.exe` est genere
- [ ] `libusb-1.0.dll` est presente dans le bundle
- [ ] Le package demarre sur une machine de test propre
- [ ] Le package affiche un message visible en cas d'echec de preflight Tk

## Runtime et logs

- [ ] `%LOCALAPPDATA%\WireWall\` ou `.wirewall-runtime\WireWall\` est cree
- [ ] `logs\wirewall.log` existe
- [ ] `exports\` existe
- [ ] `config\config.json` est present et lisible

## Tests

- [ ] `python -m pytest -q tests` passe
- [ ] Les nouveaux tests de release couvrent health checks, chemins runtime, config invalide, logging et startup preflight
