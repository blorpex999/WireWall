# Simulation d'attaque USB pour la demo

Objectif: obtenir un effet de demo credible quand un disque USB externe est branche, sans utiliser de malware reel.

## Principe

WireWall peut detecter un marqueur de simulation place a la racine d'un support USB en `Mode reel` ou en `Mode demo`.

Marqueurs reconnus:

- `WIREWALL_DEMO_THREAT.txt`
- `WIREWALL_ATTACK_SIMULATION.txt`
- `wirewall_demo_payload.bat`
- `wirewall_demo_payload.ps1`
- `wirewall_demo_payload.exe`

Important: WireWall ne lance jamais ces fichiers. Il regarde uniquement si un marqueur existe.

## Preparation du disque

Brancher le disque USB externe, puis lancer PowerShell depuis le dossier du projet:

```powershell
.\scripts\prepare_demo_usb_payload.ps1 -DriveLetter E:
```

Remplacer `E:` par la lettre du disque externe.

Le script cree:

- `WIREWALL_DEMO_THREAT.txt`: marqueur inoffensif detecte par WireWall
- `wirewall_demo_payload.bat`: petit script inoffensif qui ecrit seulement un log sur le support si on le lance manuellement

## Demo conseillee

1. Ouvrir WireWall.
2. Activer `Mode demo`.
3. Laisser l'application redemarrer sur la base demo.
4. Brancher le disque USB externe prepare.
5. Attendre un cycle de scan.
6. Ouvrir `Alertes`.
7. Montrer l'alerte `Simulation d'attaque USB`.
8. Ouvrir ou commenter l'incident associe.

Phrase a dire en mode reel:

> Le disque est vraiment branche au poste. Il ne contient pas de malware reel: il contient un marqueur inoffensif qui simule un support suspect. WireWall detecte ce marqueur et declenche le workflow reel: alerte, incident, recommandation et trace.

Phrase a dire en mode demo:

> Ce disque ne contient pas de malware reel. Il contient un marqueur inoffensif qui simule un support suspect. WireWall le detecte et declenche le meme workflow: alerte, incident, recommandation et trace.

## Ce qu'il ne faut pas faire

- ne pas utiliser de vrai malware
- ne pas activer d'autorun
- ne pas executer un programme inconnu
- ne pas presenter cela comme une attaque reelle

## Pourquoi ce choix est meilleur

- aucun risque pour le poste
- scenario reproductible devant le jury
- comportement visible dans WireWall
- separation avec la base demo `demo/wirewall_demo.db`
- discours cyber plus professionnel
