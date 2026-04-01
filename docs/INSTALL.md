# Installation WireWall

## Modes d'installation supportes

- installateur Windows `Inno Setup`
- installateur Windows `full demo` avec installeur Ollama embarque
- package portable `zip`
- execution developpeur depuis les sources

## Prerequis poste cible

### Obligatoires

- Windows 10 ou 11 x64
- droits d'ecriture utilisateur sur `%LOCALAPPDATA%`
- acceptation de l'elevation UAC au lancement de WireWall

### Optionnels selon les fonctions

- Ollama local pour l'analyse IA
- acces Internet initial si vous voulez installer Ollama ou telecharger un modele via `winget` / `ollama pull`
- un installeur Ollama officiel offline si le poste cible n'a ni `winget` ni acces Internet

### Non requis sur poste cible si vous utilisez le package ou l'installateur

- Python
- `pip`
- dependances Python du projet

## Option 1 - Installateur

Lancer :

```bat
WireWall-Setup-<version>.exe
```

L'installateur :

- copie l'application dans `Program Files`
- cree les raccourcis menu demarrer
- installe les outils d'assistance IA et de diagnostic prerequis dans le dossier `tools\` de l'application
- laisse l'application creer `%LOCALAPPDATA%\WireWall` au premier lancement
- lancera ensuite WireWall avec demande d'elevation UAC par defaut

Il n'embarque pas :

- Ollama
- le modele local

## Option 1 bis - Installateur full demo

Lancer :

```bat
WireWall-Setup-<version>-full.exe
```

Cette variante :

- installe WireWall comme l'installeur standard
- embarque aussi `tools\OllamaSetup.exe`
- permet a `Assistant IA locale` de reutiliser cet installeur local sans `winget`

Elle n'embarque toujours pas :

- le modele `qwen2.5:14b`

## Option 2 - Portable

Dezipper :

```text
WireWall-<version>-win64-portable.zip
```

Puis lancer :

```bat
WireWall.exe
```

Le package portable demandera aussi l'elevation UAC par defaut au lancement.

Le package portable contient aussi :

- `README.md`
- `CHANGELOG.md`
- `docs\`
- `tools\setup_ai.ps1`
- `tools\setup_ai.bat`
- `tools\check_target_prereqs.ps1`
- `tools\check_target_prereqs.bat`

## Option 3 - Sources

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python scripts\check_runtime.py --require-python 3.11 --require-qt
copy config.example.json %LOCALAPPDATA%\WireWall\config\config.json
python main.py
```

En mode source, WireWall tente automatiquement une relance admin. Si tu refuses l'UAC, l'application s'arrete proprement.

## Configuration IA locale

Option recommandee :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\setup_ai.ps1 -Model qwen2.5:14b
```

Ou depuis le repo :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_ai.ps1 -Model qwen2.5:14b
```

Le script :

- detecte Ollama
- reutilise `tools\OllamaSetup.exe` s'il est present
- tente son installation via `winget` si besoin
- telecharge le modele recommande
- laisse l'application utilisable sans IA si une etape echoue

Si vous disposez d'un installeur Ollama offline officiel :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\setup_ai.ps1 -Model qwen2.5:14b -OfflineInstallerPath C:\Temp\OllamaSetup.exe
```

## Diagnostic poste cible

Le package installe aussi un diagnostic simple :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\check_target_prereqs.ps1 -Model qwen2.5:14b
```

Ou via le raccourci menu demarrer `Diagnostic prerequis`.

## Emplacements runtime

Par defaut, WireWall utilise :

- `%LOCALAPPDATA%\WireWall\data\wirewall.db`
- `%LOCALAPPDATA%\WireWall\demo\wirewall_demo.db`
- `%LOCALAPPDATA%\WireWall\logs\wirewall.log`
- `%LOCALAPPDATA%\WireWall\exports\`
- `%LOCALAPPDATA%\WireWall\config\config.json`

Fallback :

- `.wirewall-runtime\WireWall\` si `%LOCALAPPDATA%` n'est pas accessible

## Desinstallation

L'installateur desinstalle les fichiers applicatifs sous `Program Files`.

Les donnees utilisateur sous `%LOCALAPPDATA%\WireWall` sont conservees par defaut pour ne pas detruire :

- la base d'audit
- les exports
- les logs
- la configuration locale

Si vous voulez une suppression complete, supprimez aussi manuellement `%LOCALAPPDATA%\WireWall` apres desinstallation.
