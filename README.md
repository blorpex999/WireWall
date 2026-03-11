# WireWall 1.1.0

WireWall est une application desktop Windows de supervision USB orientee cybersecurite. Le projet combine detection USB reelle via `PyUSB` avec backend `libusb1`, journalisation `SQLite`, scoring de risque, policies whitelist/blacklist, controle reel `USBSTOR`, analyse IA locale via Ollama et exports d'audit `HTML`, `CSV`, `JSON`.

## Formats de distribution

- developpement source depuis le repo
- bundle `PyInstaller` one-folder
- package portable `zip`
- installateur Windows `Inno Setup`

## Verites importantes

- WireWall fonctionne sans Ollama. L'analyse IA est optionnelle et strictement locale.
- Ollama et le modele recommande `qwen2.5:3b` ne sont pas embarques dans l'executable, le package portable ni l'installateur.
- La strategie IA reelle est une installation en deux phases :
  - installer WireWall
  - lancer l'assistant IA local seulement si vous voulez activer l'analyse
- `USBSTOR` bloque le stockage USB, pas tous les peripheriques USB.
- Le monitoring USB reste un monitoring utilisateur par snapshots `PyUSB/libusb1`, pas un driver noyau.

## Baseline supportee

- Windows 10 ou 11 x64
- Python 3.11 x64 pour les usages source et build
- Tcl/Tk fonctionnel pour Tkinter
- Inno Setup 6 sur le poste builder si vous voulez produire l'installateur
- Ollama local seulement si l'analyse IA doit etre utilisee

## Demarrage rapide depuis les sources

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python scripts\check_runtime.py --require-python 3.11 --require-tk
copy config.example.json %LOCALAPPDATA%\WireWall\config\config.json
python main.py
```

## Build et distribution

### Validation de base

```bat
python -m pytest -q tests
python scripts\check_runtime.py --require-python 3.11 --require-tk
python scripts\check_release_consistency.py
```

### Build executable

```bat
scripts\build.bat
```

### Package portable

```bat
scripts\package_portable.bat
```

### Installateur Windows

```bat
scripts\build_installer.bat
```

Prerequis builder :

- build `PyInstaller` valide
- Inno Setup 6 installe avec `ISCC.exe`

### Release complete

```bat
scripts\release.bat
```

Le pipeline genere :

- `dist\WireWall\`
- `release\WireWall-<version>-win64-portable.zip`
- `release\WireWall-Setup-<version>.exe`
- `release\WireWall-<version>-manifest.json`
- `release\SHA256SUMS.txt`

## Strategie IA locale

Mode recommande pour un autre poste :

1. installer ou dezipper WireWall
2. lancer l'application sans IA si necessaire
3. executer `tools\setup_ai.bat` ou `tools\setup_ai.ps1`
4. laisser l'assistant :
   - detecter Ollama
   - installer Ollama via `winget` si possible
   - telecharger `qwen2.5:3b`

Si `winget` est indisponible ou si le poste est offline, l'assistant bascule en mode guide et indique clairement quoi faire. Vous pouvez aussi fournir un installeur Ollama offline officiel au script PowerShell.

## Scripts principaux

- `scripts\run_dev.bat` : lancement source en mode reel
- `scripts\run_demo.bat` : lancement source en mode demo
- `scripts\run_admin.bat` : lancement source eleve pour les tests `USBSTOR`
- `scripts\test.bat` : suite `pytest`
- `scripts\build.bat` : build `PyInstaller`
- `scripts\package_portable.bat` : zip portable versionne
- `scripts\build_installer.bat` : compilation Inno Setup
- `scripts\release_check.bat` : validation tests + coherence release + build bundle
- `scripts\release.bat` : pipeline de release complet
- `scripts\validate_artifacts.bat` : verification des artefacts de release
- `scripts\check_release_consistency.py` : verification docs/package/version/scripts
- `scripts\check_target_prereqs.ps1` : diagnostic prerequis poste cible
- `scripts\setup_ai.ps1` : assistant IA local
- `scripts\check_ollama.ps1` : diagnostic Ollama/modele

## Discipline release

Avant chaque release :

1. mettre a jour `VERSION` si la distribution ou le comportement changent
2. mettre a jour `CHANGELOG.md`
3. mettre a jour `README.md` et les guides impactes
4. executer `scripts\release.bat` sur un builder Windows 10/11 avec Python 3.11 et Tcl/Tk valide
5. verifier les artefacts et les hashes

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Installation Windows](docs/INSTALL.md)
- [Configuration](docs/CONFIGURATION.md)
- [Utilisation rapide](docs/USAGE.md)
- [Build](docs/BUILD.md)
- [Release](docs/RELEASE.md)
- [Guide de demo Ydays](docs/DEMO_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Checklist de validation](docs/VALIDATION_CHECKLIST.md)
- [Limites techniques](docs/LIMITATIONS.md)
- [Changelog](CHANGELOG.md)
