# Limites techniques reelles

## Runtime

- WireWall supporte `Python 3.11` avec `PyQt6` fonctionnel.
- Le poste utilise pendant la finalisation expose `Python 3.13` et n'est pas un environnement de demo ou de build officiel pour l'UI.

## USB / PyUSB

- `PyUSB/libusb1` depend des descripteurs exposes par le materiel et les pilotes.
- Certaines chaines USB peuvent etre absentes, inaccessibles ou incoherentes.
- WireWall ne fait pas d'interception kernel. La detection repose sur des snapshots utilisateur compares dans le temps.
- Le hook `WM_DEVICECHANGE` sert uniquement a accelerer le prochain scan.
- L'aide integree `Comprendre` reste pedagogique: elle n'ajoute aucune preuve technique supplementaire au monitoring.

## USBSTOR

- `USBSTOR` ne bloque que le stockage USB.
- L'effet peut ne pas etre immediat sur un support deja monte.
- Selon le contexte Windows, une reinsertion du peripherique ou une nouvelle session peut etre necessaire.
- WireWall demande maintenant une session admin au lancement ; si l'UAC est refusee, l'application ne demarre pas.

## Verrouillage total USB

- Le verrouillage total applique des policies Microsoft dans `HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceInstall\Restrictions` avec application retroactive aux peripheriques deja installes.
- Il renseigne les listes `DenyDeviceClasses`, `DenyDeviceIDs` et `DenyInstanceIDs` pour couvrir a la fois familles USB, peripheriques futurs et peripheriques deja observes.
- Il active aussi `HKLM\SOFTWARE\Policies\Microsoft\Windows\RemovableStorageDevices\Deny_All` pour refuser l'acces aux stockages amovibles.
- Le verrouillage total agit sur des services Windows de controle/hub USB (`USBXHCI`, `USBHUB3`, `usbhub`, `UCX01000` si presents).
- Il desactive aussi les peripheriques USB deja presents via `pnputil`/`Disable-PnpDevice` (`USB`, `USBSTOR`, `HID\VID...`) pour rendre l'action visible sans attendre un redemarrage quand Windows l'autorise.
- Il peut bloquer souris, clavier, hubs, stockage, adaptateurs et certains peripheriques internes relies en USB.
- WireWall sauvegarde les valeurs de demarrage originales, les policies preexistantes et les IDs PnP modifies avant blocage, puis propose une restauration.
- `gpupdate` est execute pendant l'action pour privilegier la fiabilite; WireWall ne declenche jamais de redemarrage automatique, meme si certains pilotes peuvent demander un redemarrage manuel pour appliquer ou annuler pleinement l'etat.
- Cette option reste dangereuse sur un poste sans clavier/touchpad non USB ou sans acces distant.

## Ollama

- Ollama n'est pas embarque avec WireWall.
- Le modele recommande `qwen2.5:14b` n'est pas embarque non plus.
- L'installation IA sur un autre poste reste une deuxieme phase guidee, pas une installation silencieuse monolithique.
- Meme avec l'installateur `full`, seul l'installeur officiel Ollama peut etre embarque proprement, pas le modele lui-meme.
- L'analyse IA ne fonctionne que si le service local repond sur `localhost`.
- En cas d'indisponibilite, WireWall retourne un diagnostic et ne fabrique pas de resultat.
- Le `Precheck reel` peut signaler un probleme Ollama ou modele attendu, mais ne telecharge rien automatiquement.

## Cerveau local, baseline et suggestions

- Le "cerveau" WireWall repose sur une memoire locale `SQLite`, pas sur un apprentissage autonome du code.
- Les suggestions restent supervisees et ne sont jamais appliquees silencieusement.
- La baseline par peripherique reste locale au poste et a son historique ; elle n'est pas partagee entre machines.
- Deux peripheriques strictement identiques sans numero de serie peuvent rester ambigus.

## Notifications et demarrage auto

- Les notifications WireWall sont des notifications locales de l'application, pas des toasts integres a Windows Action Center.
- Le demarrage automatique utilise `HKCU\\Run`, pas un service Windows.
- Si le poste applique des restrictions de registre utilisateur, l'activation du demarrage auto peut echouer proprement.

## Packaging

- Un build PyInstaller genere sur un host dont PyQt6 est casse n'est pas une validation exploitable de l'UI.
- La validation finale du package doit etre faite sur un poste Windows propre avec `Python 3.11`, `PyQt6` valide, `libusb` et les droits adequats.
- Le bundle `dist\WireWall\` seul n'est pas une experience complete d'installation.
- La documentation et les assistants de prerequis sont ajoutes dans le package portable et l'installateur, pas dans le seul dossier `dist\WireWall\`.
- L'installateur n'efface pas automatiquement `%LOCALAPPDATA%\WireWall` a la desinstallation pour eviter de perdre audit, logs, exports et configuration.
