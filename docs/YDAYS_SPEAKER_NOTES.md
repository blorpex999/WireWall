# Notes orateur Ydays - WireWall

Support oral pour une soutenance de 25 minutes, demo incluse.

## Repartition retenue

- Orateur 1: ouverture, probleme, solution, limites honnetes, conclusion
- Orateur 2: fonctionnement, architecture, conduite principale de la demo
- Membre 3: intervention courte sur baseline / alertes / incident
- Membre 4: intervention courte sur IA locale / limites / valeur cyber
- Membre 5: intervention courte sur packaging / tests / preparation demo

## Timing global

- slides 1 a 7: 14 minutes environ
- slide 8 + demo: 7 a 8 minutes
- slides 9 et 10: 3 minutes
- marge: 1 a 2 minutes

## Slide 1 - Titre + equipe

Qui parle:

- Orateur 1

Script:

- "Bonjour, nous allons vous presenter WireWall, un outil local de supervision USB pour poste Windows."
- "L'idee centrale est simple: voir ce qui se connecte, evaluer le risque et garder une trace exploitable."
- "Nous sommes 5 dans le groupe, avec 2 personnes qui portent la presentation et la demo aujourd'hui."

## Slide 2 - Le probleme

Qui parle:

- Orateur 1

Script:

- "Dans beaucoup de contextes, une cle USB ou un peripherique branche est un point d'entree ou au minimum un point d'incertitude."
- "Le probleme, ce n'est pas seulement l'objet physique. C'est le manque de visibilite, la difficulte a tracer, et l'absence de preuve claire apres coup."
- "Nous sommes donc partis d'un besoin concret: mieux comprendre l'exposition USB d'un poste."

Transition:

- "A partir de ce probleme, nous avons construit une reponse simple et defendable."

## Slide 3 - Notre reponse

Qui parle:

- Orateur 1

Script:

- "WireWall observe, memorise, evalue, alerte et propose."
- "Nous avons volontairement evite de promettre une automatisation totale ou une protection miracle."
- "Le produit sert d'abord a rendre la situation lisible et actionnable."

Transition:

- "Pour comprendre cette promesse, on peut resumer le fonctionnement en quelques etapes."

## Slide 4 - Comment ca marche simplement

Qui parle:

- Orateur 2

Script:

- "Le logiciel detecte d'abord les changements USB sur le poste."
- "Ensuite, il enrichit les donnees disponibles, puis il les compare a la memoire locale du poste, ce que nous appelons la baseline."
- "Cette comparaison produit un score de risque, une alerte si besoin, et parfois une suggestion a valider."

Phrase de vulgarisation a garder:

- "La baseline, c'est simplement la memoire des habitudes du poste."

## Slide 5 - Les fonctionnalites qui comptent

Qui parle:

- Orateur 2

Script:

- "Concretement, WireWall sait detecter et classifier les peripheriques USB."
- "Il peut associer un risque, ouvrir une alerte, et suivre un incident."
- "Il peut aussi agir sur USBSTOR pour bloquer le stockage USB, et proposer une analyse IA locale si elle est disponible."

Intervention Membre 3:

- "Ma contribution portait surtout sur la logique de suivi: baseline, alertes et incident pour relier la detection a une vraie lecture analyste."

Transition:

- "Comme le sujet touche a la cyber, nous avons fait tres attention a distinguer ce qui est reel de ce qui est optionnel."

## Slide 6 - Ce qui est reel, ce qui est optionnel, ce qu'on ne survend pas

Qui parle:

- Orateur 1

Script:

- "Le monitoring USB, l'historique, les alertes, les incidents et le controle USBSTOR sont des fonctions reelles du produit."
- "L'IA locale existe aussi, mais elle est optionnelle. Le logiciel continue a fonctionner sans elle."
- "Nous disons clairement que nous ne sommes pas un driver noyau, et que USBSTOR bloque le stockage USB, pas tous les peripheriques."

Intervention Membre 4:

- "L'IA locale n'agit jamais seule. Elle propose un resume et des recommandations, mais la validation reste humaine."

Transition:

- "Cette clarte se retrouve aussi dans notre architecture."

## Slide 7 - Architecture simple et credible

Qui parle:

- Orateur 2

Script:

- "L'application tourne localement sur Windows."
- "Elle s'appuie sur PyUSB et libusb1 pour la detection, SQLite pour la memoire locale, USBSTOR pour le controle de stockage, et Ollama pour l'IA locale."
- "Tout reste sur le poste. C'etait un choix important pour la credibilite de la demo et pour la confidentialite."

Transition:

- "Le plus simple maintenant est de vous montrer le logiciel."

## Slide 8 - Intro demo

Qui parle:

- Orateur 2 annonce, Orateur 1 complete

Script d'introduction:

- "On va suivre un parcours court et lisible: dashboard, peripheriques, alertes, retour dashboard, controle USB puis analyse IA si elle est disponible."
- "L'objectif n'est pas de tout montrer, mais de prouver les points utiles."

## Demo live - Trame orale

### Etape 1 - Dashboard

- Orateur 2 clique
- Orateur 1 dit:
- "Ici on voit l'etat global, les incidents ouverts, les suggestions et le precheck de demo."
- "Ce bloc nous dit tout de suite si la demo est prete: backend USB, base locale, admin, exports, IA locale."

### Etape 2 - Peripheriques

- Orateur 2 ouvre la vue
- si possible, brancher un peripherique USB
- Orateur 1 dit:
- "Cette vue separe la donnee brute lue sur le poste et l'interpretation WireWall."
- "On voit le type de peripherique, sa categorie, la baseline et le score de risque."

### Etape 3 - Alertes

- Orateur 2 ouvre la vue
- Orateur 1 dit:
- "Une alerte est un signal. Si nous voulons suivre le traitement, nous ouvrons un incident et nous ajoutons une decision analyste."

### Etape 4 - Retour Dashboard

- Orateur 2 revient au dashboard
- Orateur 1 dit:
- "Le moteur local memorise ce qu'il voit et peut proposer des suggestions supervisees que l'utilisateur valide ou rejette."

### Etape 5 - Controle USB

- Orateur 2 ouvre la vue
- Orateur 1 dit:
- "Cette partie agit sur USBSTOR. Elle concerne le stockage USB et demande l'admin."

### Etape 6 - Analyse IA

- Orateur 2 ouvre la vue si Ollama est pret
- Orateur 1 dit:
- "L'analyse IA est strictement locale. Elle propose un resume et des recommandations, mais elle ne prend pas seule les decisions."

## Slide 9 - Repartition d'equipe et apprentissages

Qui parle:

- Membre 3, Membre 4, Membre 5

Format conseille:

- 20 a 30 secondes chacun

Exemple:

- Membre 3: "J'ai surtout travaille la partie logique produit autour de la baseline, des alertes et du suivi."
- Membre 4: "Je me suis concentre sur l'IA locale, la lisibilite des limites et la coherence du discours cyber."
- Membre 5: "J'ai contribue a la preparation du livrable, aux tests et a la fiabilisation de la demo."

## Slide 10 - Conclusion

Qui parle:

- Orateur 1

Script:

- "Pour conclure, WireWall apporte trois choses: de la visibilite USB, un controle credible et une IA locale optionnelle."
- "Notre objectif n'etait pas de tout promettre, mais de demonstrer un outil utile, local et defendable."
- "Merci, nous sommes disponibles pour vos questions."

## Expressions a privilegier

- "visibilite"
- "memoire locale"
- "score de risque"
- "suivi humain"
- "diagnostic honnete"
- "outil local"

## Expressions a eviter

- "on bloque tout l'USB"
- "c'est un driver noyau"
- "l'IA decide"
- "tout est automatique"
- "c'est du temps reel kernel"

## Si le jury pose une question piege

Reponse courte recommandee:

- "Nous avons volontairement choisi une promesse plus precise: un monitoring utilisateur robuste, documente, et un controle USBSTOR reel quand les droits le permettent."
