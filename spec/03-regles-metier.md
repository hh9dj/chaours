# 03 - Règles métier

Ce document recense les règles métier à implémenter dans le moteur de calcul (FastAPI / NumPy) pour le projet d'optimisation de la DOAAT.

## 1. Règles physiques et économiques

Ces règles constituent le cœur du simulateur interactif. Elles utilisent des opérations vectorielles sur des séries temporelles (tableaux NumPy) pour reduire la latence.

### A. Calculateur de trajectoire (cycles JEPP)

Principe : un réacteur dispose d'un stock d'énergie fini mesuré en Jours Équivalent Pleine Puissance (JEPP). Le stock se consomme par cycles indépendants.

Un cycle commence au jour 0 ou au `end_day` d'un arrêt, et se termine au `end_day` de l'arrêt suivant ou à la fin de l'horizon. Chaque arrêt ASR, VP ou VD réinitialise le stock à `initial_jepp` à son `end_day`, avant la production de ce jour. La production est nulle pendant `[start_day, end_day)` et le stock reste constant pendant l'arrêt.

Entrées :

- `stock_initial_jepp` (Float) : stock au début de chaque cycle.
- `vecteur_production` (Array 1D) : profil de production demandé, facteur de charge entre 0.0 et 1.0 par jour.
- `arrets` (List) : arrêts de la tranche, utilisés pour découper les cycles et recharger le stock.

Sorties :

- `facteurs_reels` (Array 1D) : facteurs physiquement contraints par le stock.
- `jepp_restant` (Array 1D) : évolution journalière du stock, borné à 0.
- `depletion_days` (List[Int]) : premier jour en déficit de chaque cycle concerné, par ordre croissant.

```python
# Pour chaque cycle [debut, fin), la consommation demandée est cumulée
consommation_cumulee = np.cumsum(vecteur_production[debut:fin])

# Premier jour où la consommation demandée dépasse le stock du cycle
jours_deficit = np.flatnonzero(consommation_cumulee > stock_initial_jepp)
jour_deficit = debut + jours_deficit[0] if jours_deficit.size else None
```

Ce jour de déficit est le premier jour du cycle qui ne peut pas être servi entièrement. La production réelle y vaut le stock restant, puis 0 jusqu'au rechargement suivant. Une consommation cumulée exactement égale au stock en fin de cycle n'est pas un déficit.

### B. Surveillance économique (valeur d'usage contre prix spot)

Principe : signaler les périodes où le prix spot est inférieur à la valeur d'usage. Le moteur ne modifie jamais automatiquement les facteurs de charge.

Entrées :

- `valeur_usage` (Mapping[str, Float]) : seuil statique du coût d'opportunité du stock (€/MWh) pour le MVP, indexé par identifiant de tranche. La table doit contenir exactement une entrée par tranche.
- `prix_spot` (Array 1D) : prévisions des prix de marché par jour (€/MWh).

Sorties :

- `alertes` (List) : une alerte par tranche et par jour où `prix_spot < valeur_usage[plant_id]`.

```python
# Détection seule : les facteurs de charge restent inchangés
jours_sous_la_vu = np.where(prix_spot < valeur_usage[plant_id])[0]
```

La VU reste un scalaire par tranche dans le MVP. Si elle devient une série journalière, sa forme passe à `(horizon,)` et la comparaison par broadcasting reste valide sans changer la logique d'alerte.

### C. Modulation manuelle (hypothèse utilisateur)

Principe : baisse volontaire de puissance imposée par l'utilisateur via le frontend.

Entrées :

- `jour_debut` et `jour_fin` (Int) : intervalle de la modulation.
- `puissance_voulue` (Float) : facteur de charge désiré, par exemple 0.6 pour 60 %.
- `vecteur_production` (Array 1D) : profil existant.

Sorties :

- `vecteur_production` mis à jour (Array 1D).

```python
# Utilisation du slicing NumPy pour modifier directement l'intervalle donné
vecteur_production[jour_debut:jour_fin] = puissance_voulue
# Le premier jour de déficit du cycle sera recalculé par la règle A
```

### D. Limite physique du stock et modulation manuelle

Principe : le stock JEPP est une limite physique dure. Le moteur ne réduit jamais automatiquement la puissance pour étaler la consommation jusqu'à l'arrêt suivant. Il n'y a pas de stretch-out automatique.

Entrées :

- `facteurs_demandes` (Array 1D) : facteurs issus de la modulation manuelle et du masque de maintenance.
- `stock_initial_jepp` (Float) : stock disponible au début de chaque cycle.
- `arrets` (List) : arrêts de la tranche.

Sorties :

- `facteurs_reels` (Array 1D) : facteurs bornés par le stock.
- `depletion_days` (List[Int]) : premier jour en déficit de chaque cycle concerné.

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

- `matrice_parc` (Array 2D) : production journalière en MWh, lignes pour les 56 tranches, colonnes pour les 365 jours.
- `demande_nationale` (Array 1D) : consommation prévue en MWh par jour.

Sorties :

- `production_totale` (Array 1D).
- `jours_deficit` (Array 1D d'index) : liste des jours où l'offre ne suffit pas.

```python
# Agrégation de toutes les tranches (lignes) jour par jour (colonnes)
production_totale = np.sum(matrice_parc, axis=0)

# Détection des jours où la production est inférieure à la demande (risque de délestage)
jours_deficit = np.where(production_totale < demande_nationale)[0]
```

## 2. Règles réglementaires et opérationnelles

### A. Transparence marché (REMIT / UMM)

Principe : surveiller la variation absolue de puissance d'un jour à l'autre, par tranche et par jour.

Entrées :

- `energie_mwh` (Array 2D) : énergie journalière par tranche, en MWh/jour.
- `arrets` (List) : arrêts planifiés, dont les bornes sont incluses dans la variation.

Sorties :

- `alertes` (List) : une alerte `REMIT_UMM` par tranche et par jour au-dessus du seuil.

Logique :

- Convertir l'énergie en puissance moyenne en divisant par 24, puis calculer la variation absolue entre deux jours consécutifs.
- Comparer cette variation au seuil de 100 MW.
- Inclure les bornes des arrêts planifiés dans la variation.
- Le jour de l'alerte est le second jour de la variation.
- La gravité est `WARNING`.

```python
# Variation absolue de puissance moyenne, par tranche
variation_mw = np.abs(np.diff(energie_mwh / 24.0, axis=1))
jours_alerte = np.where(variation_mw > 100.0)
```

### B. Contraintes du réseau haute tension (RTE)

Entrées : calendrier des arrêts programmés, données régionales des centrales.

Sorties : statut de validation du Gantt (Valide/Invalide).

Logique : empêcher le glissement d'un arrêt si cela engendre au moins 2 réacteurs arrêtés simultanément dans la même région, ou interdire l'enregistrement de l'arrêt s'il tombe entre décembre et février.

### C. Limites de compétences industrielles

Entrées : dates de début et de fin des arrêts de type ASR/VP/VD.

Sorties : nombre d'équipes mobilisées par jour et alertes de dépassement.

Logique : sommation du nombre d'arrêts en cours à un instant T. Si `arrêts_simultanés > capacité_equipes_edf`, renvoyer un conflit de ressources à l'interface.

### D. Niveaux de gravité

- `CRITICAL` : alertes neutroniques (`NEUTRONIC_ANOMALY`) et déficits nationaux (`RTE_DEFICIT`).
- `WARNING` : alertes REMIT (`REMIT_UMM`) et prix spot sous la valeur d'usage (`SPOT_BELOW_USAGE_VALUE`).
- `INFO` : réservé aux messages informatifs, sans modification des facteurs de charge.
