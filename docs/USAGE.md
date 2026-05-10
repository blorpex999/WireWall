# Utilisation rapide

## Lancement

- Mode reel : `scripts\run_dev.bat`
- Mode admin : `scripts\run_admin.bat`
- Version installee : `WireWall` via le raccourci menu demarrer
- Version portable : `WireWall.exe`
- Par defaut, WireWall demande l'elevation UAC au lancement pour exposer toutes les fonctionnalites
- Si WireWall est deja ouvert, un second lancement est refuse et la fenetre existante est reactivee si possible
- En mode source, WireWall masque la console Windows par defaut pour un rendu plus propre
- Pour garder la console de debug : `set WIREWALL_KEEP_CONSOLE=1`

## Ecrans a connaitre

- `Dashboard` : vue synthese, risque global, incidents ouverts, suggestions supervisees, sante plateforme et `Precheck reel`
- `Peripheriques` : inventaire actif, baseline locale, details, historique, whitelist et blacklist
- `Alertes` : alertes persistantes, workflow incident, commentaire analyste et resolution
- `Historique` : evenements USB, filtres et exports
- `Regles USB` : gestion de la whitelist et de la blacklist
- `Controle USB` : lecture et action sur `USBSTOR`
- `Analyse IA` : synthese locale, anomalies probables et recommandations
- `Parametres` : scan, retention, export, Ollama, profil de securite, demarrage auto et mode suggestions
- `A propos` : presentation du projet, flux de fonctionnement et lexique
- `Comprendre` : aide integree discrete sur les ecrans cles

## Flux de travail recommande

1. Verifier le `Dashboard`, le `Precheck reel` et le panneau de sante.
2. Brancher ou debrancher un peripherique USB.
3. Verifier la detection, la baseline, la source d'identification et l'historique dans `Peripheriques`.
4. Ouvrir un incident depuis `Alertes` si une alerte merite un suivi.
5. Valider ou rejeter les suggestions supervisees depuis le `Dashboard`.
6. Ajouter si besoin une regle whitelist ou blacklist.
7. Generer un export `CSV`, `JSON` ou `HTML`.
8. Lancer l'analyse IA si Ollama est disponible.
9. Verifier la demande UAC, puis tester `USBSTOR`.

## Feedbacks importants

- WireWall fonctionne uniquement en mode reel dans cette version.
- Le bouton `Comprendre` n'ajoute aucune logique metier: il sert a t'aider a expliquer l'ecran et ses limites.
- Si Ollama est indisponible, l'ecran IA affiche un diagnostic au lieu d'un faux resultat.
- Si l'elevation UAC est refusee, WireWall s'arrete au lieu de lancer une session degradee silencieuse.
- Les suggestions WireWall ne sont jamais appliquees sans validation utilisateur.
- Le demarrage automatique avec Windows reste desactive par defaut et s'active depuis `Parametres`.
- La version installee ajoute aussi des outils `Assistant IA locale` et `Diagnostic prerequis` dans le menu demarrer.
