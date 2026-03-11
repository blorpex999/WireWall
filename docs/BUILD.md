# Build WireWall

## Builder officiel

Le build officiel doit etre realise sur un poste :

- Windows 10/11 x64
- Python 3.11 x64
- Tcl/Tk fonctionnel
- Inno Setup 6 si l'installateur doit etre produit

Un poste `Python 3.13` ou un runtime Tk casse n'est pas un builder officiel, meme si un bundle peut etre produit.

## Build du bundle PyInstaller

```bat
scripts\build.bat
```

Ce script :

1. selectionne Python 3.11
2. cree `.venv` si necessaire
3. installe `requirements-dev.txt`
4. genere `build\version_info.txt`
5. lance `PyInstaller` avec `wirewall.spec`
   - workdir temporaire : `%LOCALAPPDATA%\WireWallBuilder\pyinstaller-work`
6. verifie `dist\WireWall\WireWall.exe`

## Verification de coherence release

```bat
python scripts\check_release_consistency.py
```

Ce controle verifie au minimum :

- la presence de `VERSION`
- la validite de `config.example.json`
- la presence des guides de distribution
- la coherence du packaging `PyInstaller`
- la coherence du script installateur

## Build du package portable

```bat
scripts\package_portable.bat
```

Ce script :

1. reconstruit le bundle
2. prepare un dossier de staging versionne
3. ajoute `README`, `CHANGELOG`, `docs`, `VERSION`, `config.example.json` et les outils IA/prerequis
4. genere `release\WireWall-<version>-win64-portable.zip`

## Build de l'installateur

```bat
scripts\build_installer.bat
```

Prerequis supplementaires :

- Inno Setup 6 installe
- `ISCC.exe` disponible dans :
  - `%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe`
  - ou `%ProgramFiles%\Inno Setup 6\ISCC.exe`
  - ou via la variable d'environnement `ISCC_EXE`

## Build de l'installateur full demo

```bat
scripts\build_full_installer.bat
```

Ce script :

1. construit WireWall
2. telecharge l'installeur officiel Ollama dans `build\third_party\OllamaSetup.exe`, ou reutilise le cache local s'il existe deja
3. compile un installateur `WireWall-Setup-<version>-full.exe`

Limite :

- le modele `qwen2.5:3b` n'est pas embarque ; il sera telecharge ensuite par `setup_ai`

## Release complete

```bat
scripts\release.bat
```

Ce pipeline enchaine :

1. tests
2. verification de coherence release
3. build executable
4. package portable
5. build installateur
6. manifest de release
7. hashes SHA-256
8. validation des artefacts

Variante demo :

```bat
scripts\release_full.bat
```

## Artefacts attendus

- `dist\WireWall\WireWall.exe`
- `dist\WireWall\...libusb-1.0.dll`
- `release\WireWall-<version>-win64-portable.zip`
- `release\WireWall-Setup-<version>.exe`
- `release\WireWall-Setup-<version>-full.exe`
- `release\WireWall-<version>-manifest.json`
- `release\SHA256SUMS.txt`

## Notes packaging

- Format principal : installateur Inno Setup
- Format secondaire : zip portable
- Variante demo : installateur full avec installeur Ollama embarque
- Le bundle embarque `libusb_package`, `config.example.json` et `VERSION`
- Le package portable et l'installateur embarquent aussi la documentation et les assistants IA/prerequis
- Ollama et le modele `qwen2.5:3b` ne sont pas embarques
- L'installateur full peut embarquer l'installeur officiel Ollama, mais pas un gros modele local
