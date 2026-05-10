# Runbook demo Ydays - WireWall

Trame pratique pour une demo live de 7 a 8 minutes.

## Avant de monter sur scene

- verifier que WireWall est deja lance
- verifier que la session admin a bien ete acceptee si vous voulez montrer `USBSTOR`
- verifier que l'IA locale est prete seulement si vous voulez montrer `Analyse IA`
- preparer un peripherique USB reel si possible
- fermer les fenetres parasites
- ouvrir WireWall directement sur le `Dashboard`

## Parcours demo recommande

## 1. Dashboard - 1 min

Montrer:

- risque global
- tuiles de sante
- bloc `Precheck reel`

Dire:

- "On commence par une vue globale de l'etat du poste."
- "Le precheck nous dit si la demo est prete: USB, base locale, admin, exports et IA."

## 2. Peripheriques - 1 min 30

Montrer:

- liste des peripheriques
- fiche detaillee
- baseline et score de risque

Si possible:

- brancher un peripherique USB

Dire:

- "Cette vue separe la donnee brute lue sur le poste et l'interpretation WireWall."
- "La baseline correspond a la memoire des habitudes du poste."

## 3. Alertes - 1 min 15

Montrer:

- une alerte
- le detail
- le workflow incident

Dire:

- "Une alerte est un signal. L'incident, lui, est le suivi humain associe."

## 4. Retour Dashboard - 45 sec

Montrer:

- suggestions supervisees
- synthese moteur local

Dire:

- "Le moteur local memorise, suit les deviations et propose des suggestions a valider."

## 5. Controle USB - 1 min

Montrer:

- etat USBSTOR
- si possible, lecture puis blocage ou deblocage

Dire:

- "Ici, on agit sur USBSTOR. Cela bloque le stockage USB, pas tous les peripheriques USB."

## 6. Analyse IA - 1 min 15

Montrer seulement si Ollama est pret:

- etat Ollama
- lancement de l'analyse ou resultat recent

Dire:

- "L'IA est locale et optionnelle."
- "Elle propose un resume et des recommandations, mais elle n'agit jamais seule."

## 7. Sortie demo - 15 sec

Dire:

- "On a donc montre la detection, la lecture du risque, le suivi humain, le controle USB et l'IA locale quand elle est disponible."

## Plans B

## Si Ollama n'est pas disponible

Montrer:

- l'ecran `Analyse IA`
- le diagnostic visible

Dire:

- "L'IA est optionnelle. Le logiciel reste exploitable sans elle, et le diagnostic reste honnete."

## Si la session admin n'est pas disponible

Montrer:

- l'ecran `Controle USB`
- le diagnostic non admin

Dire:

- "Le monitoring reste disponible. Seule l'action reelle sur USBSTOR est limitee."

## Si aucun peripherique USB reel n'est disponible

Montrer:

- le `Dashboard`
- `Peripheriques`
- `Alertes`

Dire:

- "Nous pouvons passer en mode reel sans melanger les donnees reelles et les donnees de demonstration."

## Si le temps se resserre

Ordre de coupe recommande:

- ne pas faire l'export en live
- ne pas lancer une nouvelle analyse IA si une ancienne suffit
- montrer `Controle USB` sans faire deux manipulations

## Rappels de discours

- ne pas promettre un driver noyau
- ne pas dire que tout l'USB est bloque
- ne pas dire que l'IA prend seule une decision
- ne pas cliquer vite: commenter ce qui est montre
- une seule personne manipule la souris

## Check final 5 minutes avant passage

- app ouverte sur `Dashboard`
- police d'affichage lisible
- cle USB a portee si prevue
- Ollama verifie si necessaire
- UAC deja geree
- notifications parasites coupees
