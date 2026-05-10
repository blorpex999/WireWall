# Diapos 20 minutes - WireWall

Trame prete a recopier dans Canva ou PowerPoint. Garder les slides visuelles: peu de texte, grandes captures, phrases courtes.

Regle simple: 1 idee par slide, 3 bullets maximum, une capture ou un schema quand c'est possible.

## Slide 1 - WireWall

Temps: 0:00 - 0:30

Titre:

`WireWall`

Sous-titre:

`Supervision USB locale pour poste Windows`

Texte affiche:

- Voir ce qui se connecte
- Evaluer le risque
- Garder une preuve exploitable

Visuel:

- capture sombre du dashboard en arriere-plan
- logo WireWall
- noms de l'equipe

Note orale:

"WireWall aide a transformer un branchement USB incertain en information lisible et exploitable."

Critere grille:

- posture professionnelle
- accroche claire

## Slide 2 - Accroche: le probleme USB

Temps: 0:30 - 3:00

Titre:

`Une cle USB inconnue pose une question simple: que vient-on de brancher ?`

Texte affiche:

- Visibilite limitee
- Risque difficile a qualifier
- Preuve difficile a retrouver

Visuel:

- photo ou pictogramme poste Windows + USB + point d'interrogation
- 3 pictos: voir, comprendre, prouver

Note orale:

"Le risque n'est pas seulement l'objet branche. Le probleme est le manque de visibilite et de tracabilite."

Critere grille:

- accroche percutante
- pitch qui retient l'attention

## Slide 3 - Notre reponse produit

Temps: 3:00 - 5:00

Titre:

`Observer, memoriser, evaluer, alerter, proposer`

Texte affiche:

- Application Windows locale
- Memoire SQLite du poste
- Decision humaine supervisee

Visuel:

- pipeline en 5 blocs
- icones simples: oeil, base, jauge, alerte, validation

Note orale:

"WireWall ne promet pas une protection magique. Il rend la situation claire, suivable et defendable."

Critere grille:

- objectifs du projet
- finalite et valeur

## Slide 4 - Comment ca marche

Temps: 5:00 - 8:00

Titre:

`Du branchement USB a l'incident`

Texte affiche:

- Detection USB -> Baseline -> Score
- Score -> Alerte -> Incident
- Suggestion -> Validation humaine

Visuel:

- frise horizontale
- definitions courtes:
  - `Baseline = habitudes du poste`
  - `Incident = suivi humain`

Note orale:

"La baseline donne du contexte. Un peripherique nouveau, rare ou blacklist n'a pas le meme niveau de risque."

Critere grille:

- presentation de la conceptualisation

## Slide 5 - Production realisee

Temps: 8:00 - 10:00

Titre:

`Ce que WireWall sait faire`

Texte affiche:

- Inventaire USB + score de risque
- Alertes, incidents, historique
- Controle USBSTOR + IA locale optionnelle

Visuel:

- 3 captures: `Peripheriques`, `Alertes`, `Controle USB`
- badges `REEL` et `DEMO`

Note orale:

"Le produit couvre le parcours complet: voir, qualifier, suivre et agir quand les droits Windows le permettent."

Critere grille:

- demonstration de la production
- branding et lisibilite

## Slide 6 - Reel vs Demo: separation nette

Temps: 10:00 - 11:30

Titre:

`Deux modes, deux bases`

Texte affiche:

- Mode reel: `data/wirewall.db`
- Mode demo: `demo/wirewall_demo.db`
- Aucun melange entre simulation et donnees reelles

Visuel:

- schema avec deux colonnes:
  - Reel: poste Windows, vrais peripheriques
  - Demo: scenario simule, cle `DEMO-ST-999`

Note orale:

"Cette separation est importante pour la credibilite cyber: les donnees de demonstration ne polluent pas les donnees reelles."

Critere grille:

- qualite de production
- capacite a expliquer les choix

## Slide 7 - Demo live

Temps: 11:30 - 16:30

Titre:

`Demo courte: peripherique suspect simule`

Texte affiche:

- Dashboard: etat global
- Peripheriques: cle suspecte
- Alertes: incident et decision

Visuel:

- grande capture du dashboard
- petite etiquette: `Scenario sans vrai malware`

Plan a suivre:

1. Dashboard: KPI + precheck
2. Peripheriques: `DEMO-ST-999`
3. Alertes: alerte + incident
4. Dashboard: suggestions
5. Controle USB: action reelle suspendue en demo
6. Analyse IA si prete

Note orale:

"On montre un cas suspect sans utiliser de peripherique dangereux. L'objectif est de prouver le comportement du logiciel."

Critere grille:

- demonstration
- gestion du temps

## Slide 8 - Impact et KPI

Temps: 16:30 - 18:00

Titre:

`Impact: moins d'incertitude, plus de trace`

Texte affiche:

- 70 tests automatises valides
- Parcours complet: detection -> incident -> export
- Donnees locales, auditables, separees

Visuel:

- jauge ou tableau KPI:
  - tests: `70 passed`
  - bases: `real/demo separees`
  - IA: `locale et optionnelle`

Note orale:

"Le ROI du projet est operationnel: gagner en visibilite, reduire l'incertitude et documenter les decisions."

Critere grille:

- mesure de l'atteinte des objectifs
- impact / KPI

## Slide 9 - Projection

Temps: 18:00 - 19:20

Titre:

`Apres les Ydays`

Texte affiche:

- Renforcer les sources Windows
- Ajouter des profils de politiques
- Industrialiser le packaging et les scenarios de test

Visuel:

- roadmap 3 etapes:
  - court terme: demo stabilisee
  - moyen terme: profils et exports
  - long terme: integration SI / SOC

Note orale:

"Le projet est aujourd'hui un demonstrateur fonctionnel. La suite serait de le rendre plus robuste, plus configurable et plus simple a deployer."

Critere grille:

- projection du projet
- besoins et developpement

## Slide 10 - Conclusion

Temps: 19:20 - 20:00

Titre:

`Ce qu'il faut retenir`

Texte affiche:

- Visibilite USB locale
- Controle defendable
- Decision humaine tracee

Visuel:

- capture finale du dashboard
- phrase courte: `Voir. Comprendre. Decider.`

Note orale:

"WireWall est un outil local, credible et honnete. Il distingue le reel, le simule, l'optionnel et les limites. Merci, nous sommes prets pour vos questions."

Critere grille:

- conclusion nette
- posture professionnelle

## Slide de secours - Limites honnetes

Ne pas montrer sauf question du jury.

Titre:

`Limites assumees`

Texte affiche:

- Pas un driver noyau
- USBSTOR bloque le stockage, pas tout l'USB
- IA locale optionnelle, jamais autonome

Reponse orale:

"Nous avons prefere une promesse precise plutot qu'une promesse trop large. Ce que WireWall fait, il le montre et le documente."

## Slide de secours - Questions difficiles

Titre:

`Questions frequentes`

Texte affiche:

- Est-ce un antivirus ? Non.
- Est-ce que ca bloque tout l'USB ? Non.
- Pourquoi un mode demo ? Pour isoler les scenarios.

Reponse orale:

"WireWall est un outil de supervision et d'aide a la decision. Il ne remplace pas une solution de securite complete, mais il rend l'exposition USB lisible."

## Checklist de creation Canva

- format 16:9
- fond sombre proche de l'application
- 3 bullets maximum par slide
- captures propres, non floues
- pas de phrases longues sur les slides
- utiliser les notes de ce fichier comme texte oral, pas comme texte affiche
- garder la slide 7 pour la demo, pas pour expliquer trop longtemps

## Captures a preparer

- Dashboard en mode demo
- Peripheriques avec `DEMO-ST-999`
- Alerte liee au scenario suspect
- Controle USB montrant les actions suspendues en demo
- Analyse IA ou diagnostic Ollama

## Correspondance avec la grille

| Grille | Slides |
|---|---|
| Accroche percutante | 1, 2 |
| Pitch convaincant | 2, 3 |
| Contexte projet | 3 |
| Conceptualisation | 4 |
| Demonstration / production / branding | 5, 6, 7 |
| ROI / KPI / impact | 8 |
| Projection | 9 |
| Presentation orale globale | toutes, surtout 7 et 10 |
