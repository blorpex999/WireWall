# Script oral 20 minutes - WireWall

Objectif: viser le niveau excellent de la grille en montrant un projet clair, utile, maitrise et defendable.

Format recommande:

- 20 minutes maximum
- 14 a 15 minutes de presentation
- 4 a 5 minutes de demo
- 30 secondes de conclusion
- garder 1 minute de marge si une transition prend du temps

## Repartition conseillee

- Orateur 1: accroche, probleme, valeur, limites honnetes, conclusion
- Orateur 2: fonctionnement, architecture, demo
- Membre 3: baseline, alertes, incidents
- Membre 4: IA locale, securite, limites
- Membre 5: tests, packaging, preparation demo

Si vous etes seulement deux a parler, gardez les interventions courtes des membres sous forme de phrases dites par Orateur 1.

## Avant de commencer

Verifier 10 minutes avant:

- WireWall ouvert sur `Dashboard`
- mode demo active si vous voulez montrer le peripherique suspect simule
- base demo separee de la base reelle: `demo/wirewall_demo.db`
- police lisible sur le projecteur
- notifications Windows fermees
- Ollama pret seulement si vous voulez montrer `Analyse IA`
- ne pas changer de mode pendant la demo, car WireWall redemarre proprement pour changer de base

Phrase de securite a garder en tete:

> En demo, les peripheriques sont simules et stockes dans une base dediee. En reel, WireWall lit le poste Windows et utilise une autre base SQLite.

## Timing global

| Temps | Partie | Objectif grille |
|---|---|---|
| 0:00 - 0:30 | Ouverture | posture professionnelle |
| 0:30 - 3:00 | Elevator pitch | accroche + pitch convaincant |
| 3:00 - 5:00 | Contexte projet | origine, objectifs, finalites |
| 5:00 - 8:00 | Conceptualisation | logique produit, architecture |
| 8:00 - 11:30 | Production | fonctionnalites, branding, qualite |
| 11:30 - 16:30 | Demo courte | preuve visible |
| 16:30 - 18:00 | Impact et KPI | resultats, tests, valeur |
| 18:00 - 19:20 | Projection | suite, besoins, developpement |
| 19:20 - 20:00 | Conclusion | reponse aux questions |

## 0:00 - 0:30 - Ouverture

Slide 1 affichee.

Orateur 1:

"Bonjour, nous allons vous presenter WireWall, notre projet Ydays. WireWall est une application Windows locale qui aide a surveiller les peripheriques USB, evaluer le risque, garder une trace et accompagner la decision humaine."

"Notre objectif aujourd'hui est simple: vous montrer le probleme, notre solution, puis une preuve courte dans le logiciel."

Transition:

"On commence par le pitch."

## 0:30 - 3:00 - Elevator pitch

Slide 2 affichee.

Orateur 1:

"Une cle USB inconnue peut sembler banale. Mais sur un poste de travail, elle pose trois questions immediates: qu'est-ce qui vient d'etre branche, est-ce habituel, et que peut-on prouver apres coup ?"

"Sans outil, on depend souvent de l'observation manuelle. On voit parfois le peripherique dans Windows, mais on n'a pas toujours une lecture claire du risque, une memoire locale, ou un suivi d'incident."

"WireWall repond a ce besoin avec une approche locale: observer, memoriser, evaluer, alerter et proposer. L'application ne promet pas de bloquer tout l'USB ni de remplacer un EDR. Elle donne une visibilite claire et defendable sur l'exposition USB d'un poste Windows."

Phrase forte:

"Le but n'est pas de dramatiser une cle USB. Le but est de transformer un branchement incertain en information exploitable."

Transition:

"Pour comprendre pourquoi nous avons construit ca, il faut revenir au contexte du projet."

## 3:00 - 5:00 - Contexte projet

Slide 3 affichee.

Orateur 1:

"Le point de depart du projet vient d'un cas tres concret: dans une entreprise, une ecole ou un atelier, des peripheriques USB circulent. Certains sont legitimes, d'autres sont inconnus, et parfois personne ne sait exactement ce qui a ete branche."

"Notre finalite etait donc de faire un demonstrateur cyber credible, centre sur un poste Windows. Nous voulions un outil utilisable en local, comprehensible par un jury non specialiste, mais assez solide techniquement pour etre defendu."

"Nos objectifs etaient: detecter les peripheriques visibles, conserver un historique, evaluer le risque, gerer des regles whitelist et blacklist, suivre les alertes en incident, proposer des exports, et ajouter une IA locale optionnelle."

Transition:

"Maintenant, voici comment nous avons conceptualise le produit."

## 5:00 - 8:00 - Conceptualisation

Slide 4 affichee.

Orateur 2:

"Le fonctionnement de WireWall suit un pipeline simple. D'abord, l'application observe les changements USB. Ensuite elle enrichit les donnees disponibles: categorie, identifiants, statut et historique."

"Puis elle compare le peripherique a une baseline. La baseline, c'est la memoire des habitudes du poste. Un peripherique jamais vu n'a pas le meme sens qu'un clavier connu depuis plusieurs sessions."

"Ensuite, un score de risque est calcule. Ce score combine les regles, le type de peripherique, la baseline, les metadonnees disponibles et le contexte. Si le score depasse un seuil, WireWall cree une alerte et peut l'associer a un incident."

Intervention membre 3:

"La partie importante pour nous etait de relier la detection a un suivi humain. Une alerte seule n'est pas suffisante. L'incident permet de documenter la decision et de garder une trace."

Transition:

"Cette conception se retrouve dans la production finale."

## 8:00 - 11:30 - Production realisee

Slide 5 affichee.

Orateur 2:

"Cote production, WireWall est une application desktop Windows en PyQt6. L'interface est organisee autour de vues de travail: Dashboard, Peripheriques, Alertes, Historique, Controle USB, Analyse IA, Regles et Parametres."

"La detection s'appuie sur PyUSB et libusb1. La memoire locale utilise SQLite. Le controle USBSTOR permet d'agir sur le stockage USB quand la session a les droits necessaires. L'analyse IA passe par Ollama, en local, et reste optionnelle."

"Nous avons aussi travaille le mode demo. Il permet de simuler un peripherique suspect sans utiliser de vrai malware et sans melanger les donnees. Le mode reel utilise `data/wirewall.db`, le mode demo utilise `demo/wirewall_demo.db`."

Intervention membre 4:

"Nous avons fait attention a l'honnetete technique. USBSTOR bloque le stockage USB, pas tous les peripheriques. L'IA propose une analyse, mais elle ne prend jamais de decision seule."

Intervention membre 5:

"Nous avons aussi prepare la stabilite: tests automatises, documentation, guides de demo et packaging Windows."

Transition:

"On passe maintenant a une demonstration courte."

## 11:30 - 16:30 - Demo courte

Slide 6 affichee: "Demo live".

Important: ne pas improviser. Suivre exactement ces etapes.

### Etape 1 - Dashboard - 45 secondes

Action:

- afficher `Dashboard`
- montrer le badge `MODE DEMO` ou `MODE REEL`
- montrer les KPI et le precheck

Orateur 2:

"Ici, on commence par le tableau de bord. Il donne une vue globale: risque, peripheriques actifs, incidents, alertes et suggestions."

Orateur 1:

"Le precheck est important pour la soutenance: il dit ce qui est pret, ce qui est limite, et ce qui depend du poste."

### Etape 2 - Peripheriques - 1 minute

Action:

- ouvrir `Peripheriques`
- selectionner la cle simulee `DEMO-ST-999` si vous etes en mode demo
- montrer categorie, baseline, score

Orateur 2:

"Ici, WireWall liste les peripheriques observes. En mode demo, nous avons une cle USB suspecte simulee. Elle n'est pas dangereuse: elle sert uniquement a reproduire un cas de risque."

Orateur 1:

"On distingue la donnee brute, comme VID/PID ou numero de serie, et l'interpretation WireWall: categorie, confiance, baseline et score."

### Etape 3 - Alertes - 1 minute

Action:

- ouvrir `Alertes`
- selectionner l'alerte liee au peripherique suspect
- montrer le detail et l'incident

Orateur 2:

"Comme ce peripherique correspond a une regle de risque, WireWall cree une alerte."

Orateur 1:

"Une alerte est un signal. L'incident est le suivi humain: on peut documenter ce qui a ete analyse, la decision et la resolution."

### Etape 4 - Retour Dashboard - 45 secondes

Action:

- revenir au `Dashboard`
- montrer suggestions ou moteur d'analyse continu

Orateur 2:

"Le dashboard se met a jour avec les alertes, incidents et suggestions."

Orateur 1:

"Ce qui nous interesse, ce n'est pas seulement la detection. C'est la boucle complete: observer, comprendre, tracer, decider."

### Etape 5 - Controle USB - 45 secondes

Action:

- ouvrir `Controle USB`
- montrer le diagnostic
- si mode demo, montrer que les actions reelles sont suspendues
- si mode reel admin, montrer la lecture USBSTOR sans forcement cliquer bloquer

Orateur 2:

"Cette partie concerne USBSTOR. Elle peut bloquer le stockage USB, mais pas tous les peripheriques USB."

Orateur 1:

"En mode demo, les actions reelles sont volontairement desactivees. C'est une preuve que nous separons bien simulation et action sur le poste."

### Etape 6 - Analyse IA - 45 secondes

Action:

- ouvrir `Analyse IA`
- montrer l'etat Ollama ou lancer l'analyse seulement si tout est pret

Orateur 2:

"L'analyse IA est locale et optionnelle. Si Ollama est pret, elle resume la situation et propose des recommandations."

Orateur 1:

"L'IA n'agit jamais seule. Elle aide l'analyste, mais la validation reste humaine."

Transition:

"La demo montre le parcours principal. On termine avec les resultats mesurables et la suite."

## 16:30 - 18:00 - Impact et KPI

Slide 7 affichee.

Orateur 1:

"Pour mesurer l'atteinte de nos objectifs, nous avons plusieurs indicateurs."

"Premier indicateur: le logiciel couvre le parcours complet que nous visions: detection, historique, scoring, alertes, incidents, controle USBSTOR, exports et IA locale optionnelle."

"Deuxieme indicateur: la qualite technique. La suite de tests automatisee passe avec 70 tests valides. Cela couvre notamment le controle des modes reel et demo, les services, l'IA, les repositories et le lancement."

"Troisieme indicateur: l'impact utilisateur. L'interface rend visible ce qui est souvent flou: quels peripheriques sont presents, quel risque est calcule, quelle action est possible, et quelles limites existent."

Phrase a dire:

"Notre ROI n'est pas financier ici. Il est operationnel: moins d'incertitude, plus de tracabilite, et une decision plus rapide."

## 18:00 - 19:20 - Projection

Slide 8 affichee.

Orateur 2:

"A la sortie des Ydays, le projet est un demonstrateur fonctionnel. Les prochaines etapes seraient de renforcer la detection Windows avec des sources systeme supplementaires, ameliorer les exports d'audit, et preparer une installation plus simple pour des postes de test."

"Il y aurait aussi un travail possible sur les profils de politiques: poste etudiant, poste administratif, poste sensible. Chaque profil aurait des seuils et regles adaptes."

"Enfin, si le projet devait continuer, nous documenterions un protocole de test avec plusieurs peripheriques reels et des scenarios de reponse incident."

## 19:20 - 20:00 - Conclusion

Slide 9 affichee.

Orateur 1:

"Pour conclure, WireWall apporte trois choses: de la visibilite USB, une memoire locale exploitable, et une aide a la decision."

"Nous avons choisi une promesse claire: un outil local, credible, qui distingue ce qui est reel, ce qui est simule, ce qui est optionnel et ce qui a des limites."

"Merci pour votre attention. Nous sommes prets a repondre a vos questions."

## Questions probables du jury

### Est-ce que WireWall bloque tout l'USB ?

"Non. WireWall agit sur USBSTOR, donc sur le stockage USB. Les claviers, souris, hubs ou autres peripheriques non stockage ne sont pas bloques par cette action."

### Est-ce un antivirus ou un EDR ?

"Non. C'est un outil local de supervision USB et d'aide a la decision. Il apporte de la visibilite, du scoring, du suivi et de l'audit."

### Pourquoi un mode demo ?

"Pour montrer un cas suspect sans utiliser de vrai peripherique dangereux et sans melanger les donnees. Le mode demo utilise une base separee."

### Pourquoi SQLite ?

"SQLite suffit pour un poste local, reste simple a deployer, fonctionne sans serveur et permet des exports auditables."

### L'IA peut-elle prendre une decision ?

"Non. L'IA locale resume et recommande. Elle ne modifie pas les regles et ne declenche pas seule une action."

### Quelle est la principale limite ?

"WireWall n'est pas un driver noyau. Il fait un monitoring utilisateur documente. C'est volontairement une promesse precise et defendable."

## A ne pas dire

- "On bloque tout l'USB."
- "C'est un antivirus."
- "L'IA decide."
- "C'est infaillible."
- "C'est un driver kernel."

## A dire souvent

- "outil local"
- "donnees separees"
- "decision humaine"
- "diagnostic honnete"
- "preuve exploitable"
