# 02 - Concepts

## Simulation et tranche

Une simulation est un ensemble isolé de paramètres et de plans de production. Elle contient :

- un nom ;
- un horizon exprimé en jours ;
- une série journalière de prix spot ;
- une série journalière de demande nationale ;
- une série journalière de valeur d'usage ;
- une ou plusieurs tranches.

Une tranche appartient à une seule simulation. Elle contient :

- un identifiant interne ;
- un code EIC ;
- une puissance nominale en MW ;
- un stock JEPP initial ;
- zéro ou plusieurs arrêts ;
- zéro ou plusieurs modulations.

Deux simulations peuvent décrire la même tranche physique avec des paramètres différents. Leurs calendriers et leurs résultats restent indépendants.

## Physique du réacteur et notion économique pivot

### Stock combustible : le JEPP

Un réacteur nucléaire fonctionne avec un stock fini d'énergie par campagne d'assemblages d'uranium, contrairement à une centrale au gaz.

Définition : 1 JEPP est l'énergie consommée par une tranche à 100 % de sa puissance nominale pendant 24 heures.

Équation de décharge :

$$S_i(t+1) = S_i(t) - \frac{P_i(t)}{P_{n,i}} \cdot \Delta t$$

Si une tranche tourne à 50 % de sa puissance nominale pendant 24 heures, elle ne consomme que 0,5 JEPP.

### Cycles JEPP et rechargement

Le stock se consomme par cycles indépendants. Un cycle commence au jour 0 ou au `jour_fin` d'un arrêt, et se termine au `jour_fin` de l'arrêt suivant ou à la fin de l'horizon.

Chaque arrêt ASR, VP ou VD réinitialise le stock à `jepp_initial` à son `jour_fin`. La production est nulle pendant `[jour_debut, jour_fin)` et le stock reste constant pendant l'arrêt. Une tranche peut avoir plusieurs arrêts, donc plusieurs cycles, sur l'horizon.

La consommation demandée est cumulée par cycle. Le premier jour où elle dépasse le stock est le jour de déficit. Ce jour-là, la production est limitée au stock restant, puis nulle jusqu'au rechargement suivant. Le stock JEPP est une limite physique dure.

Une déplétion ne déclenche aucun stretch-out automatique. Le moteur lève une alerte `NEUTRONIC_ANOMALY` et l'utilisateur corrige la trajectoire par une modulation manuelle. Une déplétion sans arrêt futur lève aussi une alerte.

### Arbitrage temporel et valeur d'usage

L'arbitrage temporel consiste à conserver du combustible en été, quand la demande et les prix spot sont bas ou négatifs, pour le restituer en hiver, période de tension et de prix forts.

La valeur d'usage (VU) représente le coût d'opportunité du MWh nucléaire, c'est-à-dire le gain financier futur estimé d'un MWh conservé en stock. Elle est exprimée en €/MWh, comme le prix spot, ce qui permet une comparaison directe.

Dans le MVP, la VU est une série temporelle journalière nationale unique pour toute la simulation. Elle n'est pas rattachée à une tranche. La série a la même longueur que l'horizon et que la série de prix spot.

Règle de surveillance économique :

- Prix spot supérieur à la VU : aucun signalement.
- Prix spot inférieur à la VU : lever une alerte informative nationale pour ce jour. La modulation de puissance reste exclusivement manuelle.

## Arrêts de tranche et contraintes

Un réacteur doit s'arrêter périodiquement pour recharger son combustible et réaliser sa maintenance sous le contrôle de l'ASN.

Types d'arrêt :

- ASR (Arrêt Simple pour Rechargement) : environ 30 à 45 jours, rechargement et contrôles simples.
- VP (Visite Partielle) : environ 60 à 90 jours, rechargement et maintenance préventive approfondie.
- VD (Visite Décennale) : 3 à 6 mois, grandes épreuves de sûreté pour la réautorisation d'exploiter 10 ans.

Contraintes de planning :

- Incapacité d'épuisement à zéro : un réacteur ne doit pas tomber à 0 JEPP avant sa date d'arrêt programmée.
- Goulots de compétences : le nombre d'intervenants spécialisés, soudeurs et prestataires, est limité et ils ne peuvent pas être simultanément sur plusieurs sites.
- Contraintes réseau (RTE) : ne pas couper plusieurs tranches d'une même région pour éviter les congestions ou les baisses de tension.
- Exclusion hivernale : éviter le chevauchement des arrêts entre décembre et février.

## Modulation manuelle

La modulation est une baisse volontaire de puissance imposée par l'utilisateur. En l'absence de modulation, le facteur de charge vaut 1.0, soit 100 %.

Une fenêtre de modulation est définie par :

- un jour de début inclus ;
- un jour de fin exclu ;
- un facteur de charge cible entre 0.0 et 1.0.

Une modulation ne peut pas chevaucher une autre modulation de la même tranche. Deux fenêtres qui se touchent sont autorisées : le jour de début de la seconde peut être égal au jour de fin de la première.

Les arrêts et les modulations appartiennent à l'entrée de tranche de la simulation. Ils ne dupliquent pas l'identifiant de la tranche dans le modèle métier.

## Résultats calculés

Les résultats d'une simulation sont calculés à la demande. Ils ne sont pas persistés dans la base de données. Ils comprennent notamment :

- les facteurs de production réels par tranche et par jour ;
- l'énergie journalière par tranche ;
- le stock JEPP restant par tranche et par jour ;
- les jours d'épuisement JEPP ;
- l'offre nationale journalière ;
- les jours de déficit national ;
- les alertes par tranche et les alertes nationales.
