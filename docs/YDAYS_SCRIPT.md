# Script de soutenance Ydays

## Version 5 minutes

### 1. Ouvrir le tableau de bord

Dire:

"WireWall surveille l'exposition USB d'un poste Windows. Ici on voit l'etat global, les incidents ouverts, les suggestions et le precheck de demo."

### 2. Montrer le precheck demo

Dire:

"Ce bloc me dit tout de suite si ma demo est prete: backend USB, base locale, exports, droits admin, Ollama et modele attendu."

### 3. Brancher un peripherique USB

Passer sur `Peripheriques`.

Dire:

"Cette vue separe la donnee brute lue sur le poste et l'interpretation WireWall. On voit le VID:PID, la categorie, la baseline et le score de risque."

### 4. Montrer une alerte

Passer sur `Alertes`.

Dire:

"Une alerte signale un risque. Si je veux suivre le traitement, j'ouvre un incident et j'ajoute une decision analyste."

### 5. Revenir au dashboard

Dire:

"Le moteur local memorise ce qu'il voit, suit les deviations et peut proposer des suggestions que l'utilisateur valide ou rejette."

## Version 10 minutes

### 1. Faire la demo 5 minutes

Puis ajouter:

### 2. Regles USB

Dire:

"Je peux mettre un peripherique en whitelist ou blacklist de facon persistante."

### 3. Controle USB

Dire:

"Ici, on agit sur USBSTOR. Cela bloque le stockage USB, pas tous les peripheriques USB. Cette partie demande l'admin."

### 4. Analyse IA

Dire:

"L'analyse IA est locale via Ollama. Elle propose un resume et des recommandations, mais elle n'agit jamais seule."

### 5. Export

Dire:

"Je peux exporter l'etat du poste en HTML, JSON ou CSV avec un hash d'audit pour rendre le rapport plus defensable."

## Ce qu'il faut eviter de promettre

- ne pas parler de driver noyau
- ne pas dire que tout l'USB est bloque par USBSTOR
- ne pas dire que l'IA prend les decisions
- ne pas dire que l'installateur embarque toujours le modele local
- ne pas dire que toutes les metadonnees USB sont garanties

## Plan B si quelque chose tombe

### Ollama absent

Dire:

"L'IA est optionnelle. Le logiciel reste exploitable sans elle, et l'ecran montre un diagnostic honnete."

### Pas d'admin

Dire:

"Le monitoring reste disponible. Seul le controle reel USBSTOR est limite."

### Aucun USB reel

Dire:

"Je passe en mode demo pour montrer les flux sans melanger les donnees reelles du poste."
