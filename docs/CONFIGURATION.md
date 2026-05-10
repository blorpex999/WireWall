# Configuration WireWall

## Fichier de configuration

Le fichier local de configuration est attendu dans :

`%LOCALAPPDATA%\WireWall\config\config.json`

La version officielle de l'application est stockee dans `VERSION`. Elle n'est pas ecrite dans `config.json`.

Vous pouvez aussi lancer l'application avec :

```bat
python main.py --config C:\chemin\vers\config.json
```

Le fichier d'exemple fourni est `config.example.json`.

## Parametres principaux

- `mode` : toujours force a `real`
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
- `autostart_enabled` : active le lancement WireWall avec Windows via `HKCU\Run`
- `desktop_notifications_enabled` : active les notifications locales discretes des alertes `HIGH` / `CRITICAL`
- `recommendation_mode` : `conservative`, `balanced`, `proactive`
- `author_name` et `organization_name` : metadonnees d'affichage

## Profils de securite

- `Normal` : profil par defaut, equilibre entre sensibilite et stabilite
- `Strict` : scans plus frequents, seuil d'alerte plus bas
- `Presentation` : scans plus stables et fenetre anti-doublon plus large pour une presentation plus lisible

Les valeurs `scan_interval_seconds`, `alert_threshold` et `dedup_window_seconds` sont recalibrees selon le profil choisi.

## Baseline, incidents et suggestions

- La baseline locale est calculee automatiquement par peripherique a partir des reconnexions et des plages horaires observees.
- Les etats visibles sont `NEW`, `RARE`, `KNOWN` et `DEVIATION`.
- Le `recommendation_mode` ajuste l'agressivite des suggestions supervisees :
  - `conservative` : moins de suggestions, plus de prudence
  - `balanced` : mode recommande
  - `proactive` : suggestions plus frequentes
- Les decisions analyste (`whitelist`, `blacklist`, `watch`, `trusted`) sont memorisees localement.

## Conseils de configuration terrain

- Conserver `mode: "real"` pour les tests terrain
- Definir `export_directory` si vous voulez un dossier d'exports visible et stable pendant la soutenance
- Pour `qwen2.5:14b`, un timeout de `180` a `210` secondes est plus realiste sur un laptop milieu de gamme
- La valeur projet recommandee est `210` secondes
- Laisser `autostart_enabled` a `false` pendant la soutenance si tu veux garder un demarrage maitrise a la main

## Conseils de configuration distribution

- Ne versionnez pas votre `config.json` local depuis `%LOCALAPPDATA%`
- Laissez `ollama_model` sur `qwen2.5:14b` si vous voulez rester aligne avec les scripts et la documentation
- Si vous changez de modele recommande, mettez aussi a jour :
  - `config.example.json`
  - `README.md`
  - `docs/INSTALL.md`
  - `docs/RELEASE.md`
  - `installer/WireWall.iss`
