# 01 - Contexte

## Cadre institutionnel

- DOAAT (Direction Optimisation Amont-Aval et Trading) : chargée d'équilibrer l'offre et la demande d'électricité à moyen et long terme.
- Pôle GPM (Gestion Portefeuille et Marchés) : équipe opérationnelle qui utilise des outils comme CHAOURS pour programmer les trajectoires de production et les arrêts de maintenance sur un horizon de 1 mois à 5 ans.

## Objectifs centraux

- Maximiser la valeur économique du portefeuille de production d'EDF.
- Garantir la sécurité d'approvisionnement électrique de la France.
- Respecter strictement la sûreté nucléaire.

## Objet de CHAOURS

CHAOURS est un simulateur interactif d'aide à la décision. Il permet de :

- tester et valider les calendriers d'arrêt des tranches nucléaires ;
- calculer la capacité physique des tranches et des centrales à partir de l'épuisement du combustible (JEPP) ;
- prendre en compte l'arbitrage temporel de la vente entre la valeur d'usage (VU) et le prix spot ;
- vérifier que la production disponible couvre la demande nationale.

## Application web

CHAOURS est une application web organisée autour de simulations isolées :

- le dashboard liste les simulations sous forme de cartes et permet d'en créer une nouvelle ;
- une simulation contient un horizon, des séries journalières nationales et plusieurs tranches ;
- chaque tranche possède un calendrier d'arrêts et de modulations ;
- une timeline par tranche montre la production, les arrêts, les modulations et le niveau de JEPP ;
- les alertes propres à une tranche sont affichées sur sa timeline ;
- les alertes nationales sont regroupées dans une barre latérale dédiée à la simulation.

Les modifications d'une simulation sont isolées des autres simulations. Les résultats de calcul, comme les alertes, les jours de déficit, les jours d'épuisement JEPP et l'offre journalière, ne sont pas persistés : ils sont recalculés à l'ouverture de la simulation et après chaque modification.
