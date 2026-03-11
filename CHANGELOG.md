# Changelog

## 1.1.0 - 2026-03-11

- Consolidation de la chaine de distribution Windows avec une source de version unique via `VERSION`.
- Ajout d'un garde-fou de coherence release pour verifier scripts, docs, packaging et ressources obligatoires avant generation des artefacts.
- Alignement de l'installateur Inno Setup avec les vrais chemins runtime `%LOCALAPPDATA%\WireWall`.
- Ajout d'une distribution portable versionnee incluant la documentation et les assistants IA.
- Ajout d'assistants Windows pour verifier les prerequis poste cible et configurer Ollama/le modele local.
- Renforcement des scripts de build et de release pour limiter la dependance au `python` systeme courant.
- Mise a jour complete de `README.md`, des guides d'installation, build, release, troubleshooting et validation cible.

## 1.0.0 - 2026-03-11

- Base WireWall fonctionnelle : supervision USB Windows, scoring, policies, audit et UI desktop.
- Packaging `PyInstaller` one-folder et documents initiaux de build et de demo.
