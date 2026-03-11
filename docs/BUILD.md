# Build WireWall

## Builder officiel

Le build de release doit etre realise sur un poste :

- Windows 10/11 x64
- Python 3.11 x64
- `Tcl/Tk` fonctionnel

Un host Python 3.13 ou un runtime Tk casse n'est pas un builder officiel, meme si un bundle sort.

## Commande officielle

```bat
scripts\build.bat
```

Le script :

1. verifie Python 3.11 et Tkinter
2. cree `.venv` si necessaire
3. installe `requirements-dev.txt`
4. lance `python -m PyInstaller --clean --noconfirm wirewall.spec`
5. verifie la presence de `dist\WireWall\WireWall.exe`

## Verification release complete

```bat
scripts\release_check.bat
```

Ce script enchaine :

1. tests `pytest`
2. build PyInstaller
3. verification de `WireWall.exe`
4. verification de `libusb-1.0.dll` dans le bundle

## Artefacts attendus

- `dist\WireWall\WireWall.exe`
- `dist\WireWall\_internal\libusb-1.0.dll` ou equivalent dans le bundle
- `config.example.json` embarque

## Notes packaging

- Format officiel : `PyInstaller one-folder`
- Pas de MSI, pas d'installateur, pas de signature de code dans ce lot
- La documentation du repo n'est pas embarquee dans le bundle final
