# Architecture WireWall

## Vue d'ensemble

WireWall suit une architecture en couches :

- `app/models` : dataclasses metier et types de transport
- `app/core` : classification USB, moteur de risque, niveaux de criticite
- `app/infrastructure` : SQLite, config, logging, registre Windows, chemins
- `app/services` : enumeration USB, monitoring, policies, controle USB, IA locale, rapports, retention, health checks, jobs asynchrones
- `app/ui` : application PyQt6, controleur, vues, widgets, theme
- `app/utils` : dates, validation, elevation, helpers Windows

## Flux applicatif

1. `main.py` verifie d'abord le runtime PyQt6.
2. `app/bootstrap.py` charge la configuration, prepare les chemins, initialise SQLite, repositories et services.
3. `UsbMonitorService` tourne dans un thread dedie et produit des snapshots USB.
4. Chaque snapshot est compare au snapshot precedent.
5. Les evenements, assessments et alertes sont persistants en base.
6. `EventBus` transporte les notifications vers l'UI.
7. L'UI consomme les evenements via `QTimer` sans acces direct des threads de fond aux widgets.
8. Les appels potentiellement bloquants comme les health checks reseau et l'analyse Ollama passent par `BackgroundTaskService`.

## Persistance

- Base reelle : `%LOCALAPPDATA%\\WireWall\\data\\wirewall.db`
- Base demo : `%LOCALAPPDATA%\\WireWall\\demo\\wirewall_demo.db`
- Fallback portable : `.wirewall-runtime\\WireWall\\...` si le repertoire standard n'est pas accessible
- Journal SQLite en mode `WAL`
- Retention appliquee sur `device_events`, `alerts`, `risk_assessments`, `ai_analyses`

## Detection USB

- Source de verite : `PyUSB` avec backend `libusb1`
- Resolution de DLL `libusb-1.0.dll` priorisee sur :
  - `_MEIPASS` en mode PyInstaller
  - dossier de l'executable
  - package `libusb_package`
- Le hook Windows `WM_DEVICECHANGE` ne remplace pas le snapshot : il declenche seulement un refresh rapide
- Un scan USB en echec ne provoque pas de faux `disconnected` ; l'etat precedent est conserve et un evenement `scan_error` est journalise

## Controle USB storage

- Cle cible : `HKLM\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR\\Start`
- `3` : stockage USB autorise
- `4` : stockage USB bloque
- Lecture avant action, ecriture, puis relecture de verification
- Les diagnostics distinguent `permission_denied`, `not_found`, `mismatch`, `error`

## IA locale

- Ollama est interroge via `http://127.0.0.1:11434`
- Health check via `GET /api/tags`
- Analyse via `POST /api/generate`
- Aucun appel reseau Internet
- Les erreurs reseau ou de modele sont remontees a l'utilisateur sans faux succes
