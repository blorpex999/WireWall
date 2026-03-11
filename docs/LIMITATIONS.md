# Limites techniques reelles

## Runtime

- WireWall supporte `Python 3.11` avec `Tcl/Tk` fonctionnel.
- Le poste utilise pendant la finalisation expose `Python 3.13` et n'est pas un environnement de demo ou de build officiel pour l'UI.

## USB / PyUSB

- `PyUSB/libusb1` depend des descripteurs exposes par le materiel et les pilotes.
- Certaines chaines USB peuvent etre absentes, inaccessibles ou incoherentes.
- WireWall ne fait pas d'interception kernel. La detection repose sur des snapshots utilisateur compares dans le temps.
- Le hook `WM_DEVICECHANGE` sert uniquement a accelerer le prochain scan.

## USBSTOR

- `USBSTOR` ne bloque que le stockage USB.
- L'effet peut ne pas etre immediat sur un support deja monte.
- Selon le contexte Windows, une reinsertion du peripherique ou une nouvelle session peut etre necessaire.
- Les actions de blocage et de deblocage exigent une session admin.

## Ollama

- Ollama n'est pas embarque avec WireWall.
- L'analyse IA ne fonctionne que si le service local repond sur `localhost`.
- En cas d'indisponibilite, WireWall retourne un diagnostic et ne fabrique pas de resultat.

## Packaging

- Un build PyInstaller genere sur un host dont Tkinter est casse n'est pas une validation exploitable de l'UI.
- La validation finale du package doit etre faite sur un poste Windows propre avec `Python 3.11`, `Tcl/Tk` valide, `libusb` et les droits adequats.
- Le bundle PyInstaller n'embarque pas toute la documentation du depot : les guides restent dans le repo source.
