# Utilisation rapide

## Lancement

- Mode reel : `scripts\run_dev.bat`
- Mode demo : `scripts\run_demo.bat`
- Mode admin : `scripts\run_admin.bat`
- Version installee : `WireWall` via le raccourci menu demarrer
- Version portable : `WireWall.exe`
- Si WireWall est deja ouvert, un second lancement est refuse et la fenetre existante est reactivee si possible
- En mode source, WireWall masque la console Windows par defaut pour un rendu plus propre
- Pour garder la console de debug : `set WIREWALL_KEEP_CONSOLE=1`

## Ecrans a connaitre

- `Dashboard` : vue synthese, risque global, sante plateforme, timeline et alertes
- `Peripheriques` : inventaire actif, details, whitelist et blacklist
- `Alertes` : alertes persistantes et acquittement
- `Historique` : evenements USB, filtres et exports
- `Regles USB` : gestion de la whitelist et de la blacklist
- `Controle USB` : lecture et action sur `USBSTOR`
- `Analyse IA` : analyse locale via Ollama
- `Parametres` : scan, retention, export, Ollama, profil de securite
- `A propos` : presentation du projet

## Flux de travail recommande

1. Verifier le `Dashboard` et le panneau de sante.
2. Brancher ou debrancher un peripherique USB.
3. Verifier la detection dans `Peripheriques` et `Historique`.
4. Ajouter si besoin une regle whitelist ou blacklist.
5. Generer un export `CSV`, `JSON` ou `HTML`.
6. Lancer l'analyse IA si Ollama est disponible.
7. Tester `USBSTOR` uniquement en session admin.

## Feedbacks importants

- En mode demo, l'application l'indique visuellement et la base utilisee est separee.
- Si Ollama est indisponible, l'ecran IA affiche un diagnostic au lieu d'un faux resultat.
- Si la session n'est pas admin, les actions `USBSTOR` restent explicites sur cette limite.
- La version installee ajoute aussi des outils `Assistant IA locale` et `Diagnostic prerequis` dans le menu demarrer.
