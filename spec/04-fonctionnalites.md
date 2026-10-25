# 04 - Fonctionnalités

## Exigences fonctionnelles

- Afficher l'ensemble des tranches nucléaires.
- Contrôler les plannings d'arrêt des tranches nucléaires :
  - ASR (Arrêt Simple pour Rechargement), environ 30 à 45 jours ;
  - VP (Visite Partielle), environ 60 à 90 jours ;
  - VD (Visite Décennale), environ 3 à 6 mois.
- Réinitialiser le stock JEPP d'une tranche à `initial_jepp` après chaque arrêt ASR, VP et VD, au `end_day` de l'arrêt.
- Gérer plusieurs arrêts par tranche, chaque arrêt créant un cycle JEPP indépendant.
- Calculer la réserve de production pour une date à partir de l'équation d'épuisement du combustible JEPP.
- Appliquer une limite physique dure : si la consommation demandée dépasse le stock, la production est coupée jusqu'au rechargement suivant.
- Lever une alerte `NEUTRONIC_ANOMALY` en cas de déplétion et laisser l'utilisateur corriger la trajectoire par une modulation manuelle, sans stretch-out automatique.
- Afficher la courbe de production électrique cumulée des tranches nucléaires.
- Afficher la courbe de demande.
- Détecter les périodes où la demande est supérieure à la production.
- Lever les alertes REMIT par tranche et par jour au-delà de 100 MW de variation absolue.

## Composants du simulateur

- Gantt temporel dynamique : visualisation et manipulation par glissement (drag and drop) des calendriers d'arrêt des tranches.
- Calculateur de trajectoires JEPP : recalcul en temps réel de l'épuisement du combustible après chaque modification de planning, avec rechargement à chaque fin d'arrêt.
- Moteur d'agrégation de puissance (MW) : sommation instantanée du profil d'offre national disponible face à la courbe de charge.
- Détecteur de conflits et alertes : signalement des ruptures de stock neutronique, des variations REMIT par tranche, des chevauchements de compétences et des risques de délestage.

## Critères d'acceptation

- Le calcul de décharge JEPP prend en compte la modulation, donc les MW réels par rapport aux MW nominaux.
- Le stock JEPP repart de `initial_jepp` au `end_day` de chaque arrêt ASR, VP et VD, et chaque arrêt crée un cycle indépendant.
- La production est nulle pendant un arrêt et le stock reste constant pendant l'arrêt.
- Si la consommation demandée dépasse le stock avant l'arrêt suivant, la production du jour de déficit est limitée au stock restant, puis nulle jusqu'au rechargement suivant.
- Une déplétion lève une alerte `NEUTRONIC_ANOMALY` qui demande une modulation manuelle ; aucune baisse de puissance automatique n'est appliquée.
- Une déplétion sans arrêt futur lève aussi une alerte.
- Le simulateur alerte lorsque la somme de la puissance disponible est inférieure à la pointe hivernale.
- Le simulateur alerte lorsque le prix spot est inférieur à la valeur d'usage (VU), sans modifier les facteurs de charge.
- Les alertes REMIT sont levées par tranche et par jour lorsque la variation absolue de puissance dépasse 100 MW, bornes d'arrêt incluses.
- Le moteur de simulation est séparé de l'interface graphique (IHM).
