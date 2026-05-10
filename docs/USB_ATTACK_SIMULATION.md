# Simulation d'attaque USB pour la demo

Objectif: obtenir un effet de demo credible quand un disque USB externe est branche, sans utiliser de malware reel ni d'injection systeme.

## Principe

WireWall peut detecter un marqueur de simulation place a la racine d'un support USB en `Mode reel` ou en `Mode demo`.

La preuve conseillee est une preuve d'execution controlee: le support contient un petit batch inoffensif, lance manuellement, qui ecrit seulement une trace locale dans `%TEMP%\WireWallUsbProof\usb_payload_proof.txt` et une copie de log sur le support USB.

Marqueurs reconnus:

- `WIREWALL_DEMO_THREAT.txt`
- `WIREWALL_ATTACK_SIMULATION.txt`
- `wirewall_demo_payload.bat`
- `wirewall_demo_payload.ps1`
- `wirewall_demo_payload.exe`

Important: WireWall ne lance jamais ces fichiers. Il regarde uniquement si un marqueur existe. Le batch est optionnel et doit etre lance manuellement pendant la demo si vous voulez prouver que du code place sur un support USB peut modifier l'environnement utilisateur.

## Preparation du disque

Brancher le disque USB externe, puis lancer PowerShell depuis le dossier du projet:

```powershell
.\scripts\prepare_demo_usb_payload.ps1 -DriveLetter E:
```

Remplacer `E:` par la lettre du disque externe.

Le script cree:

- `WIREWALL_DEMO_THREAT.txt`: marqueur inoffensif detecte par WireWall
- `wirewall_demo_payload.bat`: petit script inoffensif qui ecrit seulement une preuve locale dans `%TEMP%` et un log sur le support si on le lance manuellement

## Demo conseillee

1. Ouvrir WireWall.
2. Verifier que le badge indique `REEL`.
3. Brancher le disque USB externe prepare.
4. Attendre un cycle de scan.
5. Ouvrir `Alertes`.
6. Montrer l'alerte `Simulation d'attaque USB`.
7. Ouvrir ou commenter l'incident associe.
8. Optionnel: lancer manuellement `wirewall_demo_payload.bat` depuis le support.
9. Montrer le fichier `%TEMP%\WireWallUsbProof\usb_payload_proof.txt`.

Phrase a dire:

> On ne lance pas de malware. On prouve qu'un support USB peut contenir du code executable et modifier l'environnement utilisateur en ecrivant une trace locale. WireWall detecte le support comme scenario suspect et declenche l'alerte.

Variante si vous restez en mode demo:

1. Ouvrir WireWall.
2. Activer `Mode demo`.
3. Laisser l'application redemarrer sur la base demo.
4. Brancher le disque USB externe prepare.
5. Montrer que le meme scenario cree une alerte dans une base separee.

Phrase a dire en mode demo:

> Ce disque ne contient pas de malware reel. Il contient un marqueur inoffensif qui simule un support suspect. WireWall le detecte et declenche le meme workflow: alerte, incident, recommandation et trace.

## Ce qu'il ne faut pas faire

- ne pas utiliser de vrai malware
- ne pas activer d'autorun
- ne pas executer un programme inconnu
- ne pas presenter cela comme une infection reelle
- ne pas parler d'injection systeme si le batch ecrit seulement une trace utilisateur

## Pourquoi ce choix est meilleur

- aucun risque pour le poste
- scenario reproductible devant le jury
- comportement visible dans WireWall
- preuve concrete que du code peut etre execute depuis le support
- separation possible avec la base demo `demo/wirewall_demo.db`
- discours cyber plus professionnel
