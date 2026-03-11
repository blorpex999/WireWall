# Changelog

## 1.2.1 - 2026-03-11

- Ajout d'un verrou Windows d'instance unique pour empecher l'ouverture simultanee de plusieurs fenetres WireWall.
- Lors d'un second lancement, l'application informe l'utilisateur et tente de reactiver la fenetre deja ouverte.
- Mise a jour de la documentation d'usage et de troubleshooting pour decrire ce comportement.

## 1.2.0 - 2026-03-11

- Ajout d'une variante de distribution "full demo" avec installeur WireWall capable d'embarquer l'installeur officiel Ollama quand il est disponible au build.
- Ajout d'un script de telechargement de l'installeur Ollama pour le builder Windows.
- Ajout d'un script `release_full.bat` pour produire une distribution de demo plus autonome.
- Mise a jour de l'assistant IA pour reutiliser automatiquement l'installeur Ollama embarque s'il est present dans `tools\OllamaSetup.exe`.
- Mise a jour de la documentation de distribution pour distinguer le package standard du package demo "full".

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
