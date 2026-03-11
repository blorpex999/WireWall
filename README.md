# WireWall

WireWall est une application desktop Windows de supervision USB orientee cybersecurite. Le projet combine detection USB reelle via `PyUSB` avec backend `libusb1`, journalisation `SQLite`, scoring de risque, policies whitelist/blacklist, controle reel `USBSTOR`, analyse IA locale via Ollama et exports d'audit `HTML`, `CSV`, `JSON`.

## Perimetre reel

- Detection des branchements et debranchements USB par snapshots `PyUSB/libusb1`
- Inventaire des peripheriques avec classification metier
- Policies persistantes par `VID:PID` et numero de serie si disponible
- Scoring, criticite, alertes et historique persistants
- Blocage/deblocage reel du stockage USB via `HKLM\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR`
- Analyse IA locale uniquement via Ollama sur `localhost`
- Rapports d'audit `HTML`, `CSV`, `JSON`
- Mode demo isole avec base de donnees distincte

## Baseline supportee

- Windows 10 ou 11 x64
- Python 3.11 x64
- `Tcl/Tk` fonctionnel pour Tkinter
- Ollama installe localement si l'ecran IA doit etre demontre

Le poste utilise pendant cette finalisation expose `Python 3.13` et n'est pas l'hote officiel de release. Les scripts et la documentation ciblent donc explicitement `Python 3.11`.

## Demarrage rapide

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python scripts\check_runtime.py --require-python 3.11 --require-tk
copy config.example.json %LOCALAPPDATA%\WireWall\config\config.json
python main.py
```

## Scripts batch

- `scripts\run_dev.bat` : lancement source en mode reel
- `scripts\run_demo.bat` : lancement source en mode demo
- `scripts\run_admin.bat` : lancement source eleve pour les tests `USBSTOR`
- `scripts\test.bat` : execution de la suite `pytest`
- `scripts\build.bat` : build `PyInstaller one-folder`
- `scripts\release_check.bat` : verification release tests + build + artefacts
- `scripts\clean.bat` : nettoyage des artefacts generes

## Validation rapide

```bat
python -m compileall main.py app tests
python -m pytest -q tests
python scripts\check_runtime.py --require-python 3.11 --require-tk
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Installation Windows](docs/INSTALL.md)
- [Configuration](docs/CONFIGURATION.md)
- [Utilisation rapide](docs/USAGE.md)
- [Guide de build](docs/BUILD.md)
- [Guide de demo Ydays](docs/DEMO_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Checklist de validation](docs/VALIDATION_CHECKLIST.md)
- [Limites techniques](docs/LIMITATIONS.md)

## Verites importantes

- Le monitoring USB est base sur des snapshots utilisateur. Le hook `WM_DEVICECHANGE` accelere le refresh, mais WireWall n'intercepte pas le noyau Windows.
- `USBSTOR` bloque le stockage USB, pas l'ensemble des classes USB.
- Certaines chaines fabricant, produit et serie dependent du materiel, du pilote et des permissions.
- L'analyse IA est locale. Si Ollama ne repond pas, WireWall n'invente pas de resultat.
- Le build PyInstaller officiel doit etre genere sur un poste `Python 3.11 + Tcl/Tk` reellement valide.
