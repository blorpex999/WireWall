# Configuration WireWall

## Fichier de configuration

Le fichier local de configuration est attendu dans :

`%LOCALAPPDATA%\WireWall\config\config.json`

Vous pouvez aussi lancer l'application avec :

```bat
python main.py --config C:\chemin\vers\config.json
```

Le fichier d'exemple fourni est `config.example.json`.

## Parametres principaux

- `mode` : `real` ou `demo`
- `scan_interval_seconds` : frequence de polling USB
- `history_retention_days` : retention des evenements, alertes, assessments et analyses IA
- `log_level` : `INFO`, `WARNING`, `ERROR`, `DEBUG`
- `ollama_base_url` : URL locale d'Ollama, par defaut `http://127.0.0.1:11434`
- `ollama_model` : modele local a utiliser
- `ollama_timeout_seconds` : timeout HTTP de l'analyse IA
- `security_profile` : `Normal`, `Strict`, `Presentation`
- `export_directory` : dossier de sortie des exports et rapports
- `alert_threshold` : seuil d'alerte
- `dedup_window_seconds` : fenetre anti-doublon des evenements
- `dashboard_refresh_ms` : cadence de rafraichissement de l'UI
- `author_name` et `organization_name` : metadonnees d'affichage

## Profils de securite

- `Normal` : profil par defaut, equilibre entre sensibilite et stabilite
- `Strict` : scans plus frequents, seuil d'alerte plus bas
- `Presentation` : scans plus stables et fenetre anti-doublon plus large pour une demo plus lisible

Les valeurs `scan_interval_seconds`, `alert_threshold` et `dedup_window_seconds` sont recalibrees selon le profil choisi.

## Conseils de configuration demo

- Conserver `mode: "real"` pour les tests terrain
- Utiliser `scripts\run_demo.bat` pour un scenario demo separe
- Definir `export_directory` si vous voulez un dossier d'exports visible et stable pendant la soutenance
- Garder `ollama_timeout_seconds` raisonnable pour eviter une attente trop longue en demo
