# 04 - Fonctionnalités

## Exigences fonctionnelles

- Afficher l'ensemble des tranches nucléaires.
- Contrôler les plannings d'arrêt des tranches nucléaires :
  - ASR (Arrêt Simple pour Rechargement), environ 30 à 45 jours ;
  - VP (Visite Partielle), environ 60 à 90 jours ;
  - VD (Visite Décennale), environ 3 à 6 mois.
- Réinitialiser les capacités d'une tranche nucléaire après finalisation d'un arrêt.
- Permettre un stretch-out pour prolonger une campagne avec une puissance dégradée.
- Calculer la réserve de production pour une date à partir de l'équation d'épuisement du combustible JEPP.
- Afficher la courbe de production électrique cumulée des tranches nucléaires.
- Afficher la courbe de demande.
- Détecter les périodes où la demande est supérieure à la production.

## Composants du simulateur

- Gantt temporel dynamique : visualisation et manipulation par glissement (drag and drop) des calendriers d'arrêt des tranches.
- Calculateur de trajectoires JEPP : recalcul en temps réel de l'épuisement du combustible après chaque modification de planning.
- Moteur d'agrégation de puissance (MW) : sommation instantanée du profil d'offre national disponible face à la courbe de charge.
- Détecteur de conflits et alertes : signalement des ruptures de stock neutronique, des chevauchements de compétences et des risques de délestage.

## Critères d'acceptation

- Le calcul de décharge JEPP prend en compte la modulation, donc les MW réels par rapport aux MW nominaux.
- Le simulateur alerte lorsque la somme de la puissance disponible est inférieure à la pointe hivernale.
- Le simulateur alerte lorsque le prix spot est inférieur à la valeur d'usage (VU), sans modifier les facteurs de charge.
- Le moteur de simulation est séparé de l'interface graphique (IHM).
