# Troubleshooting

## `check_runtime.py` echoue

Cause probable :

- Python 3.11 absent
- `Tcl/Tk` non fonctionnel

Action :

```bat
py -3.11 -c "import tkinter; tkinter.Tk().destroy()"
```

Si cette commande echoue, changez de poste ou reinstallez Python 3.11 avec Tcl/Tk.

## L'application ne demarre pas en package

Cause probable :

- Build realise sur un host non supporte
- Runtime Tk incomplet

Action :

- refaire le build sur un poste `Python 3.11 + Tcl/Tk` valide
- verifier `dist\WireWall\WireWall.exe`
- verifier la presence de `libusb-1.0.dll` dans `dist\WireWall`

## Aucun peripherique USB n'apparait

Cause probable :

- aucun peripherique compatible branche
- backend `libusb1` indisponible
- descripteurs materiels limites

Action :

- verifier le panneau `Health`
- verifier le message `usb_backend`
- utiliser le mode demo si aucun vrai materiel n'est disponible

## Ollama indisponible

Cause probable :

- service local non lance
- modele absent
- URL de base incorrecte

Action :

- lancer Ollama localement
- verifier `http://127.0.0.1:11434`
- tester depuis l'ecran `Analyse IA`
- en soutenance, expliquer que l'analyse est strictement locale et facultative

## `USBSTOR` ne change pas d'effet

Cause probable :

- session non admin
- support deja monte
- contexte Windows qui requiert une reinsertion ou une nouvelle session

Action :

- lancer `scripts\run_admin.bat`
- refaire la lecture d'etat dans `Controle USB`
- debrancher/rebrancher le support

## Les fichiers runtime ne sont pas crees sous `%LOCALAPPDATA%`

Cause probable :

- repertoire non accessible ou politique de securite du poste

Action :

- verifier si WireWall a bascule sur `.wirewall-runtime\WireWall\`
- verifier les permissions OneDrive ou poste de demo
