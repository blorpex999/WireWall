# Release WireWall

## Objectif

Ce document decrit la chaine officielle de distribution Windows pour WireWall.

## Formats de distribution

- format principal : installateur `Inno Setup`
- format secondaire : archive portable `zip`
- format demo autonome : installateur `Inno Setup` avec installeur Ollama embarque
- format developpeur : execution depuis les sources

## Source de verite de version

- Le numero de version officiel est stocke dans `VERSION`
- Cette version est reutilisee par :
  - l'application
  - les artefacts de release
  - l'installateur
  - le manifest de release
  - le changelog

## Pipeline officiel

Sur un builder Windows valide :

```bat
scripts\release.bat
```

Le pipeline execute :

1. `scripts\test.bat`
2. `scripts\check_release_consistency.py`
3. `scripts\build.bat`
4. `scripts\package_portable.bat`
5. `scripts\build_installer.bat`
6. `scripts\write_release_manifest.py`
7. `scripts\write_release_hashes.ps1`
8. `scripts\validate_artifacts.bat`

Variante demo :

```bat
scripts\release_full.bat
```

Si `dist\WireWall\` est deja a jour mais que tu veux seulement regenerer le portable et les installateurs sans relancer PyInstaller, utilise :

```bat
scripts\release_from_dist.bat
```

## Artefacts attendus

- `dist\WireWall\`
- `release\WireWall-<version>-win64-portable.zip`
- `release\WireWall-Setup-<version>.exe`
- `release\WireWall-Setup-<version>-full.exe`
- `release\WireWall-<version>-manifest.json`
- `release\SHA256SUMS.txt`

## Prerequis builder

- Windows 10/11 x64
- Python 3.11 x64
- PyQt6 valide
- Inno Setup 6 si l'installateur doit etre produit

## Ollama en release

- Ollama n'est pas embarque dans l'executable ni dans l'installateur
- Le modele `qwen2.5:14b` n'est pas embarque
- La strategie officielle est :
  - installer WireWall
  - executer l'assistant IA local si necessaire
  - laisser l'application fonctionner sans IA si Ollama n'est pas disponible
- Les dossiers runtime utilisateur sont crees par l'application au premier lancement, pas par l'installateur.

Pour la release demo `full` :

- l'installeur officiel Ollama peut etre embarque
- le modele n'est toujours pas embarque
- l'assistant IA local reste responsable du telechargement du modele

## Git et synchronisation

Routine conseillee avant push :

1. mettre a jour `VERSION`
2. mettre a jour `CHANGELOG.md`
3. mettre a jour `README.md` et les guides impactes
4. executer `scripts\release.bat`
5. verifier les artefacts dans `release\`
6. commit
7. push

Exemple :

```bat
git status
git add VERSION CHANGELOG.md README.md docs scripts installer wirewall.spec
git commit -m "release: prepare WireWall <version>"
git push origin main
```

## Discipline de synchronisation

Avant toute release :

- mettre a jour `VERSION` si le comportement ou la distribution changent
- mettre a jour `CHANGELOG.md`
- mettre a jour `README.md`
- mettre a jour les docs impactees
- regenerer les artefacts
- verifier `SHA256SUMS.txt`
