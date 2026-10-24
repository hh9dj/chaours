# 02 - Concepts

## Physique du réacteur et notion économique pivot

### Stock combustible : le JEPP

Un réacteur nucléaire fonctionne avec un stock fini d'énergie par campagne d'assemblages d'uranium, contrairement à une centrale au gaz.

Définition : 1 JEPP est l'énergie consommée par une tranche à 100 % de sa puissance nominale pendant 24 heures.

Équation de décharge :

$$S_i(t+1) = S_i(t) - \frac{P_i(t)}{P_{n,i}} \cdot \Delta t$$

Si une tranche tourne à 50 % de sa puissance nominale pendant 24 heures, elle ne consomme que 0,5 JEPP.

### Arbitrage temporel et valeur d'usage

L'arbitrage temporel consiste à conserver du combustible en été, quand la demande et les prix spot sont bas ou négatifs, pour le restituer en hiver, période de tension et de prix forts.

La valeur d'usage (VU) représente le coût d'opportunité du MWh nucléaire, c'est-à-dire le gain financier futur estimé d'un MWh conservé en stock. Elle est exprimée en €/MWh, comme le prix spot, ce qui permet une comparaison directe.

La VU dépend de la tranche, de son cycle de combustible et de son stock restant. Elle peut aussi évoluer dans le temps avec les prévisions météo et les marchés à terme.

Règle de surveillance économique :

- Prix spot supérieur à la VU : aucun signalement.
- Prix spot inférieur à la VU : lever une alerte informative. La modulation de puissance reste exclusivement manuelle.

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
