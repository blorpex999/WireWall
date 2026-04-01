# Presentation Canva Ydays - WireWall

Support de soutenance en francais pour un jury mixte cyber / non-cyber.

## Cadre retenu

- duree cible: 22 a 23 minutes utiles + marge questions
- duree totale: 25 minutes demo incluse
- angle: probleme concret -> solution -> preuve par la demo
- niveau: vocabulaire accessible avec explication courte des termes techniques
- format: Canva, 16:9, 10 slides + 1 slide de secours non montree par defaut

## Direction visuelle Canva

- fond principal: tres sombre, proche de l'interface WireWall
- accent principal: bleu clair pour la structure et les titres
- accent secondaire: vert pour les preuves positives, orange pour les alertes, rouge uniquement pour les limites ou les risques
- privilegier une grande capture annotee plutot que beaucoup de texte
- 1 idee par slide, 3 bullets max par slide
- afficher une courte definition des mots techniques a leur premiere apparition

Palette suggeree:

- fond: `#0F141B`
- panneau: `#161D27`
- texte: `#EDF1F6`
- bleu: `#28A1FF`
- vert: `#67C587`
- orange: `#F0BE52`
- rouge: `#FF657D`

## Slide 1 - Titre + equipe

Objectif:

- installer le sujet en une phrase simple
- montrer que le projet est porte collectivement

Texte a afficher:

- `WireWall`
- `Surveiller et controler l'exposition USB d'un poste Windows`
- `<Nom 1> - <Nom 2> - <Nom 3> - <Nom 4> - <Nom 5>`

Visuel recommande:

- logo ou capture du dashboard en arriere-plan legerement assombrie
- ligne discrete "Projet Ydays"

Message oral:

- "WireWall aide a voir ce qui se connecte en USB, a evaluer le risque et a garder une trace exploitable."

Timing / parole:

- 1 min
- Orateur 1

## Slide 2 - Le probleme

Objectif:

- partir d'un risque concret et universel

Texte a afficher:

- `Une cle USB inconnue peut introduire un risque sur un poste.`
- `Sans visibilite claire, on subit au lieu de comprendre.`
- `Sans historique, il est difficile de prouver ce qui s'est passe.`

Visuel recommande:

- illustration tres simple: poste Windows + USB + point d'interrogation
- ou photo d'une cle USB avec 3 bulles: visibilite, risque, preuve

Message oral:

- "Le probleme n'est pas seulement de brancher un USB. Le vrai probleme, c'est de savoir quoi faire, quoi tracer et quoi expliquer."

Timing / parole:

- 2 min
- Orateur 1

## Slide 3 - Notre reponse

Objectif:

- donner la promesse produit sans survendre

Texte a afficher:

- `Observer`
- `Memoriser`
- `Evaluer`
- `Alerter`
- `Proposer`

Sous-titre:

- `WireWall est un outil local de supervision USB, pas une solution magique.`

Visuel recommande:

- 5 blocs ou 5 etapes avec une icone par action

Message oral:

- "Notre objectif n'etait pas de tout bloquer automatiquement, mais d'offrir une vision claire, une memoire locale et des actions defensables."

Timing / parole:

- 2 min
- Orateur 1

## Slide 4 - Comment ca marche simplement

Objectif:

- expliquer le pipeline sans entrer trop vite dans la technique

Texte a afficher:

- `Detection USB -> Enrichissement -> Baseline -> Score -> Alerte / Incident -> Suggestion`
- `Baseline = memoire des habitudes du poste`
- `Incident = suivi humain`
- `Suggestion supervisee = recommandation a valider`

Visuel recommande:

- frise horizontale avec fleches
- petites definitions sous les mots techniques

Message oral:

- "WireWall observe ce qui se passe, enrichit les donnees visibles, compare avec l'habitude du poste et transforme cela en risque lisible."

Timing / parole:

- 2 min 30
- Orateur 2

## Slide 5 - Les fonctionnalites qui comptent

Objectif:

- mettre en avant les preuves produit les plus utiles pour le jury

Texte a afficher:

- `Detection et classification des peripheriques USB`
- `Score de risque, alertes et workflow incident`
- `Controle USBSTOR + IA locale optionnelle`

Visuel recommande:

- grille en 3 colonnes avec 1 capture par bloc
- captures conseillees: `Peripheriques`, `Alertes`, `Controle USB` ou `Analyse IA`

Message oral:

- "On voulait un outil utile sur un vrai poste Windows: voir, qualifier, suivre et agir sans mentir sur ce qui est faisable."

Intervention courte:

- Membre 3, 20 a 30 secondes
- point recommande: baseline, alertes ou incident

Timing / parole:

- 2 min 30
- Orateur 2 + Membre 3

## Slide 6 - Ce qui est reel, ce qui est optionnel, ce qu'on ne survend pas

Objectif:

- rassurer le jury sur l'honnetete technique

Texte a afficher:

- `Reel: monitoring USB, historique, alertes, incident, lecture/ecriture USBSTOR`
- `Optionnel: IA locale via Ollama`
- `Important: pas de driver noyau, USBSTOR bloque le stockage USB, pas tout l'USB`

Visuel recommande:

- tableau 3 colonnes: Reel / Optionnel / Limites honnetes

Message oral:

- "Nous preferons une promesse precise et defendable plutot qu'un discours flou. Le logiciel montre ce qu'il sait faire et ne fabrique pas de faux succes."

Intervention courte:

- Membre 4, 20 a 30 secondes
- point recommande: IA locale ou limites honnetes

Timing / parole:

- 2 min
- Orateur 1 + Membre 4

## Slide 7 - Architecture simple et credible

Objectif:

- montrer que le projet est structure sans noyer le jury

Texte a afficher:

- `Application Windows locale`
- `PyUSB/libusb1 + SQLite + USBSTOR + Ollama local`
- `Tout reste local au poste, y compris l'IA`

Visuel recommande:

- schema tres simple avec 5 blocs:
- Interface
- Moteur local
- Base SQLite
- Detection USB
- Ollama local

Message oral:

- "L'architecture est volontairement locale: la detection, la memoire, les exports et l'IA restent sur la machine."

Timing / parole:

- 2 min
- Orateur 2

## Slide 8 - Demo live

Objectif:

- annoncer clairement le parcours de demo

Texte a afficher:

- `Dashboard -> Peripheriques -> Alertes -> Dashboard -> Controle USB -> Analyse IA`
- `Objectif: montrer la valeur, pas cliquer partout`
- `Plan B pret si IA, admin ou USB reel manquent`

Visuel recommande:

- liste numerotee tres lisible
- petite capture du dashboard en fond

Message oral:

- "On va suivre le chemin le plus utile pour le jury: voir, comprendre, suivre, agir, puis terminer par l'IA si elle est disponible."

Timing / parole:

- 20 a 30 secondes d'introduction
- puis demo live de 7 a 8 min
- Orateur 2 pilote, Orateur 1 commente

## Slide 9 - Repartition d'equipe et apprentissages

Objectif:

- valoriser le travail des 5 membres sans casser le rythme

Texte a afficher:

- `<Nom 1> - cadrage, discours, partie produit`
- `<Nom 2> - pilotage demo, architecture, technique`
- `<Nom 3> - baseline / alertes / incidents`
- `<Nom 4> - IA locale / limites / valeur cyber`
- `<Nom 5> - packaging / tests / preparation demo`

Visuel recommande:

- 5 cartes identiques
- 1 contribution principale par personne

Message oral:

- "Nous avons choisi une repartition orientee produit: chacun a contribue a une brique visible dans la demonstration."

Timing / parole:

- 2 min
- Membre 3 + Membre 4 + Membre 5 avec transition d'Orateur 1

## Slide 10 - Conclusion

Objectif:

- terminer sur une promesse claire et defendable

Texte a afficher:

- `Visibilite USB`
- `Controle credible`
- `IA locale optionnelle et honnete`

Phrase finale:

- `Notre objectif n'etait pas de tout promettre, mais de demonstrer un outil utile, local et defendable.`

Visuel recommande:

- fond sobre + 3 chiffres ou 3 blocs
- eventuellement une capture du dashboard final

Timing / parole:

- 1 min
- Orateur 1

## Slide de secours - Demo degradee

Ne pas afficher par defaut. La garder en backup en fin de deck.

Texte a afficher:

- `Sans Ollama: l'IA est optionnelle, le logiciel reste exploitable`
- `Sans admin: le monitoring reste visible, seul USBSTOR est limite`
- `Sans USB reel: le mode demo reste separe du mode reel`

Visuel recommande:

- 3 cartes simples avec icones de secours

Usage:

- uniquement si la demo live est degradee

## Captures d'ecran a preparer

- dashboard avec `Precheck demo` visible
- vue `Peripheriques`
- vue `Alertes`
- vue `Controle USB`
- vue `Analyse IA`

## Rappels importants pour Canva

- garder beaucoup d'air entre les blocs
- ne jamais coller une phrase longue en petit
- afficher les mots techniques en gros, leur traduction simple juste dessous
- ne pas surcharger la slide architecture
- reserver la slide 8 a la demo, pas a du texte
