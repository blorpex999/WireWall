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

- build realise sur un host non supporte
- runtime Tk incomplet

Action :

- refaire le build sur un poste `Python 3.11 + Tcl/Tk` valide
- verifier `dist\WireWall\WireWall.exe`
- verifier la presence de `libusb-1.0.dll` dans `dist\WireWall`

## Un second lancement n'ouvre pas une nouvelle fenetre

Cause probable :

- une instance WireWall est deja active

Action :

- revenir a la fenetre WireWall deja ouverte
- verifier la barre des taches Windows
- fermer l'instance existante avant de relancer si vous voulez une nouvelle session propre

## `build_installer.bat` echoue

Cause probable :

- Inno Setup 6 absent
- `ISCC.exe` introuvable

Action :

- installer Inno Setup 6
- verifier l'un de ces chemins :
  - `%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe`
  - `%ProgramFiles%\Inno Setup 6\ISCC.exe`
- ou definir `ISCC_EXE`

## `build_full_installer.bat` echoue

Cause probable :

- Inno Setup 6 absent
- echec de telechargement de `OllamaSetup.exe`
- `winget show Ollama.Ollama` indisponible

Action :

- verifier la connectivite Internet du builder
- verifier `winget show Ollama.Ollama`
- lancer `powershell -File scripts\fetch_ollama_installer.ps1` a la main
- verifier `build\third_party\OllamaSetup.exe`

## `check_release_consistency.py` echoue

Cause probable :

- `VERSION` invalide
- documentation ou scripts manquants
- packaging `wirewall.spec` desynchronise
- script installateur desynchronise

Action :

- corriger les fichiers signales
- relancer le controle avant de produire un package ou une release

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
- `winget` absent ou installeur offline non fourni

Action :

- lancer Ollama localement
- verifier `http://127.0.0.1:11434`
- tester depuis l'ecran `Analyse IA`
- lancer `tools\setup_ai.bat` ou `tools\setup_ai.ps1`
- si `winget` est absent, utiliser un installeur Ollama officiel offline avec `-OfflineInstallerPath`
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

## L'installateur a fonctionne mais l'IA locale ne marche pas

Cause probable :

- Ollama n'est pas installe
- le modele `qwen2.5:3b` n'est pas encore telecharge

Action :

- ouvrir `Assistant IA locale` depuis le menu demarrer
- ou lancer `tools\check_target_prereqs.bat` pour diagnostiquer l'etat du poste
