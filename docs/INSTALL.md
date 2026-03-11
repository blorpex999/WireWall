# Installation WireWall

## Prerequis

- Windows 10 ou 11 x64
- Python 3.11 x64
- `Tcl/Tk` fonctionnel pour Tkinter
- Droits administrateur uniquement si vous voulez agir sur `USBSTOR`
- Ollama installe localement si vous voulez utiliser l'analyse IA

## Verification du runtime

Avant de lancer WireWall :

```bat
python scripts\check_runtime.py --require-python 3.11 --require-tk
```

Si ce script echoue, ne preparez pas la demo sur ce poste.

## Installation developpeur

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
copy config.example.json %LOCALAPPDATA%\WireWall\config\config.json
```

## Lancement

- Mode reel :

```bat
scripts\run_dev.bat
```

- Mode demo :

```bat
scripts\run_demo.bat
```

- Mode eleve pour les tests `USBSTOR` :

```bat
scripts\run_admin.bat
```

## Emplacements runtime

Par defaut, WireWall cree ses donnees sous `%LOCALAPPDATA%\WireWall\` :

- `data\wirewall.db` : base reelle
- `demo\wirewall_demo.db` : base demo
- `logs\wirewall.log` : logs applicatifs
- `exports\` : rapports et exports
- `config\config.json` : configuration locale

Si ce repertoire n'est pas accessible, WireWall bascule sur un fallback portable `.wirewall-runtime\WireWall\`.

## Verification post-installation

- L'application demarre sans erreur Tkinter
- Les dossiers `data`, `logs`, `exports`, `config` sont crees
- Le dashboard charge sans freeze
- Les health checks se mettent a jour sans bloquer l'interface
- `USB Control` lit l'etat `USBSTOR`

Pour la configuration, le build et le troubleshooting, utilisez aussi :

- [Configuration](CONFIGURATION.md)
- [Build](BUILD.md)
- [Troubleshooting](TROUBLESHOOTING.md)
