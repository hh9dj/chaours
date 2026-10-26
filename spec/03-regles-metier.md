# 03 - Règles métier

Ce document décrit les règles de calcul et les critères d'acceptation métier du moteur. Les détails de schéma de données, de repository et d'API sont définis dans `backend/spec.md`.

## 1. Règles physiques et économiques

### A. Calculateur de trajectoire (cycles JEPP)

Principe : un réacteur dispose d'un stock d'énergie fini mesuré en Jours Équivalent Pleine Puissance (JEPP). Le stock se consomme par cycles indépendants.

Un cycle commence au jour 0 ou au `jour_fin` d'un arrêt, et se termine au `jour_fin` de l'arrêt suivant ou à la fin de l'horizon. Chaque arrêt ASR, VP ou VD réinitialise le stock à `jepp_initial` à son `jour_fin`, avant la production de ce jour. La production est nulle pendant `[jour_debut, jour_fin)` et le stock reste constant pendant l'arrêt.

Entrées :

- `jepp_initial` (Float) : stock au début de chaque cycle.
- `facteurs_demandes` (Array 1D) : profil de production demandé, facteur de charge entre 0.0 et 1.0 par jour.
- `arrets` (List) : arrêts de la tranche, utilisés pour découper les cycles et recharger le stock.

Sorties :

- `facteurs_reels` (Array 1D) : facteurs physiquement contraints par le stock.
- `jepp_restant` (Array 1D) : évolution journalière du stock, borné à 0.
- `jours_epuisement` (List[Int]) : premier jour en déficit de chaque cycle concerné, par ordre croissant.

```python
# Pour chaque cycle [debut, fin), la consommation demandée est cumulée
consommation_cumulee = np.cumsum(facteurs_demandes[debut:fin])

# Premier jour où la consommation demandée dépasse le stock du cycle
jours_deficit = np.flatnonzero(consommation_cumulee > jepp_initial)
jour_deficit = debut + jours_deficit[0] if jours_deficit.size else None
```

Ce jour de déficit est le premier jour du cycle qui ne peut pas être servi entièrement. La production réelle y vaut le stock restant, puis 0 jusqu'au rechargement suivant. Une consommation cumulée exactement égale au stock en fin de cycle n'est pas un déficit.

### B. Surveillance économique (valeur d'usage contre prix spot)

Principe : signaler les jours où le prix spot est inférieur à la valeur d'usage. Le moteur ne modifie jamais automatiquement les facteurs de charge.

Entrées :

- `valeur_usage_eur_mwh` (Array 1D) : série journalière nationale du coût d'opportunité du stock, en €/MWh.
- `prix_spot_eur_mwh` (Array 1D) : série journalière nationale des prix de marché, en €/MWh.

Sorties :

- `alertes` (List) : une alerte nationale par jour où `prix_spot_eur_mwh[jour] < valeur_usage_eur_mwh[jour]`.

```python
# Détection seule : les facteurs de charge restent inchangés
jours_sous_la_vu = np.where(prix_spot_eur_mwh < valeur_usage_eur_mwh)[0]
```

L'alerte est nationale : elle ne porte pas d'identifiant de tranche. La VU est une série nationale dans le MVP. Une évolution future vers une VU par tranche devra faire l'objet d'une nouvelle règle métier explicite.

### C. Modulation manuelle

Principe : baisse volontaire de puissance imposée par l'utilisateur. En l'absence de modulation, le facteur de charge par défaut vaut 1.0 (100 %).

Entrées :

- `jour_debut` et `jour_fin` (Int) : intervalle semi-ouvert de la modulation.
- `facteur` (Float) : facteur de charge désiré, par exemple 0.6 pour 60 %.
- `facteurs_demandes` (Array 1D) : profil existant.

Les arrêts et les modulations sont portés par l'entrée de tranche de la simulation à laquelle ils appartiennent. Ils ne dupliquent pas l'identifiant de tranche.

Sorties :

- `facteurs_demandes` mis à jour (Array 1D).

```python
# Utilisation du slicing NumPy pour modifier directement l'intervalle donné
facteurs_demandes[jour_debut:jour_fin] = facteur
# Le premier jour de déficit du cycle sera recalculé par la règle A
```

Deux modulations d'une même tranche ne peuvent pas se chevaucher. Deux fenêtres qui se touchent sont autorisées.

### D. Limite physique du stock et modulation manuelle

Principe : le stock JEPP est une limite physique dure. Le moteur ne réduit jamais automatiquement la puissance pour étaler la consommation jusqu'à l'arrêt suivant. Il n'y a pas de stretch-out automatique.

Entrées :

- `facteurs_demandes` (Array 1D) : facteurs issus de la modulation manuelle et du masque de maintenance.
- `jepp_initial` (Float) : stock disponible au début de chaque cycle.
- `arrets` (List) : arrêts de la tranche.

Sorties :

- `facteurs_reels` (Array 1D) : facteurs bornés par le stock.
- `jours_epuisement` (List[Int]) : premier jour en déficit de chaque cycle concerné.

Logique :

- Le premier jour où la consommation demandée dépasse le stock est le jour de déficit.
- Ce jour-là, la production réelle vaut le stock restant, puis 0 jusqu'au rechargement suivant.
- Une déplétion lève une alerte `NEUTRONIC_ANOMALY` de gravité `CRITICAL`.
- L'alerte demande à l'utilisateur de corriger la trajectoire par une modulation manuelle avant l'arrêt.
- Une déplétion sans arrêt futur lève aussi une alerte.

```python
# Aucune dégradation automatique : on applique seulement la limite physique
facteurs_reels[jour_deficit] = stock_restant
facteurs_reels[jour_deficit + 1 : fin_cycle] = 0.0
```

### E. Agrégation nationale et équilibre réseau

Principe : additionner la production de toutes les tranches nucléaires pour vérifier que la capacité couvre la demande.

Entrées :

- `matrice_par_tranche` (Array 2D) : production journalière en MWh, lignes pour les tranches, colonnes pour les jours.
- `demande_nationale_mwh` (Array 1D) : consommation prévue en MWh par jour.

Sorties :

- `offre_nationale_mwh` (Array 1D).
- `jours_deficit` (Array 1D d'index) : jours où l'offre ne suffit pas.

```python
# Agrégation de toutes les tranches (lignes) jour par jour (colonnes)
offre_nationale_mwh = np.sum(matrice_par_tranche, axis=0)

# Détection des jours où la production est inférieure à la demande
jours_deficit = np.where(offre_nationale_mwh < demande_nationale_mwh)[0]
```

## 2. Règles réglementaires et opérationnelles

### A. Transparence marché (REMIT / UMM)

Principe : surveiller la variation absolue de puissance d'un jour à l'autre, par tranche et par jour.

Entrées :

- `energie_mwh` (Array 2D) : énergie journalière par tranche, en MWh/jour.
- Les bornes des arrêts planifiés sont incluses dans la variation.

Sorties :

- `alertes` (List) : une alerte `REMIT_UMM` par tranche et par jour au-dessus du seuil.

Logique :

- Convertir l'énergie en puissance moyenne en divisant par 24, puis calculer la variation absolue entre deux jours consécutifs.
- Comparer cette variation au seuil de 100 MW.
- Le jour de l'alerte est le second jour de la variation.
- La gravité est `WARNING`.

```python
# Variation absolue de puissance moyenne, par tranche
variation_mw = np.abs(np.diff(energie_mwh / 24.0, axis=1))
jours_alerte = np.where(variation_mw > 100.0)
```

### B. Contraintes du réseau haute tension (RTE)

Entrées : calendrier des arrêts programmés, données régionales des centrales.

Sorties : statut de validation du planning.

Logique : empêcher le glissement d'un arrêt si cela engendre au moins deux réacteurs arrêtés simultanément dans la même région, ou interdire l'enregistrement de l'arrêt s'il tombe entre décembre et février.

### C. Limites de compétences industrielles

Entrées : dates de début et de fin des arrêts de type ASR, VP ou VD.

Sorties : nombre d'équipes mobilisées par jour et alertes de dépassement.

Logique : sommation du nombre d'arrêts en cours à un instant donné. Si le nombre d'arrêts simultanés dépasse la capacité d'équipes, renvoyer un conflit de ressources à l'interface.

### D. Niveaux de gravité

- `CRITICAL` : alertes neutroniques (`NEUTRONIC_ANOMALY`) et déficits nationaux (`RTE_DEFICIT`).
- `WARNING` : alertes REMIT (`REMIT_UMM`) et prix spot sous la valeur d'usage (`SPOT_BELOW_USAGE_VALUE`).
- `INFO` : réservé aux messages informatifs, sans modification des facteurs de charge.

### E. Portée des alertes

- Une alerte de tranche porte un identifiant de tranche. Elle est affichée sur la timeline de cette tranche.
- Une alerte nationale ne porte pas d'identifiant de tranche. Elle est affichée dans la barre latérale de la simulation.
- `NEUTRONIC_ANOMALY` et `REMIT_UMM` sont des alertes de tranche.
- `RTE_DEFICIT` et `SPOT_BELOW_USAGE_VALUE` sont des alertes nationales.

## 3. Critères d'acceptation métier

- Le calcul de décharge JEPP prend en compte la modulation, donc les MW réels par rapport aux MW nominaux.
- Le stock JEPP repart de `jepp_initial` au `jour_fin` de chaque arrêt ASR, VP et VD, et chaque arrêt crée un cycle indépendant.
- La production est nulle pendant un arrêt et le stock reste constant pendant l'arrêt.
- Si la consommation demandée dépasse le stock avant l'arrêt suivant, la production du jour de déficit est limitée au stock restant, puis nulle jusqu'au rechargement suivant.
- Une déplétion lève une alerte `NEUTRONIC_ANOMALY` qui demande une modulation manuelle ; aucune baisse de puissance automatique n'est appliquée.
- Une déplétion sans arrêt futur lève aussi une alerte.
- Le moteur alerte lorsque l'offre nationale disponible est inférieure à la demande nationale.
- Le moteur alerte lorsque le prix spot est inférieur à la valeur d'usage, sans modifier les facteurs de charge.
- L'alerte prix spot sous la valeur d'usage est nationale et produite une fois par jour concerné.
- Les alertes REMIT sont levées par tranche et par jour lorsque la variation absolue de puissance dépasse 100 MW, bornes d'arrêt incluses.
- Le moteur de simulation est séparé de l'interface graphique.
- Les alertes, jours de déficit, jours d'épuisement JEPP, offre journalière et énergie ne sont pas persistés.
