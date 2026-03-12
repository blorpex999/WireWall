# Comment WireWall fonctionne

## En une phrase

WireWall observe l'etat USB d'un poste Windows, memorise ce qu'il voit, calcule un risque, ouvre un incident si besoin et propose des actions sans jamais agir seul sur la partie analyse.

## Etape 1 - Observation USB

- WireWall utilise `PyUSB` avec le backend `libusb1`.
- L'application prend des snapshots de l'etat USB a intervalle regulier.
- Elle compare ces snapshots pour voir si un device est apparu, disparu ou a change.

Ce point est important: ce n'est pas un driver noyau. C'est un monitoring utilisateur honnete et documente.

## Etape 2 - Enrichissement des donnees

Pour chaque peripherique, WireWall essaie de lire:

- `VID` / `PID`
- nom constructeur et nom produit si disponibles
- numero de serie si expose
- classe USB
- bus et adresse quand ils sont accessibles

Si une information manque, WireWall ne l'invente pas. L'interface indique ce qui vient du backend et ce qui est deduit.

## Etape 3 - Classification et baseline

WireWall classe ensuite le peripherique dans une categorie metier:

- storage
- HID
- hub
- imaging
- communication
- vendor_specific
- unknown

En parallele, l'application maintient une baseline locale:

- `NEW` si le device vient d'apparaitre
- `RARE` s'il a ete peu vu
- `KNOWN` s'il est habituel
- `DEVIATION` s'il est connu mais se comporte differemment

## Etape 4 - Scoring de risque

Le moteur de regles combine:

- type de device
- policies whitelist / blacklist
- historique recent
- baseline
- metadata manquantes
- contexte d'usage

Le resultat donne:

- un score
- un niveau `LOW / MEDIUM / HIGH / CRITICAL`
- des raisons
- des recommandations de base

## Etape 5 - Alertes, incidents et suggestions

Si le contexte le justifie:

- une alerte est creee
- un incident peut etre ouvert
- l'analyste ajoute une decision et un commentaire
- des suggestions supervisees peuvent etre proposees

Important:

- l'alerte est un signal
- l'incident est le suivi humain
- la suggestion est une proposition

Rien n'est applique silencieusement.

## Etape 6 - Controle USBSTOR

WireWall peut lire et modifier `USBSTOR` sur Windows pour bloquer ou debloquer le stockage USB.

Cela signifie:

- blocage des supports de stockage USB
- pas de blocage general de tous les peripheriques USB

Cette fonction demande des droits admin. Une reinsertion du support peut etre necessaire pour voir l'effet.

## Etape 7 - IA locale

WireWall peut envoyer un contexte compact a Ollama en local pour obtenir:

- un resume
- des anomalies probables
- des recommandations

L'IA reste:

- locale
- optionnelle
- non autonome
- non decisionnaire seule

Si Ollama ne repond pas, l'application affiche un diagnostic au lieu d'un faux resultat.
