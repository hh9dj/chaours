# 03 - Règles métier

Ce document recense les règles métier à implémenter dans le moteur de calcul (FastAPI / NumPy) pour le projet d'optimisation de la DOAAT.

## 1. Règles physiques et économiques

Ces règles constituent le cœur du simulateur interactif. Elles utilisent des opérations vectorielles sur des séries temporelles (tableaux NumPy) pour reduire la latence.

### A. Calculateur de trajectoire (épuisement JEPP)

Principe : un réacteur dispose d'un stock d'énergie fini mesuré en Jours Équivalent Pleine Puissance (JEPP).

Entrées :

- `stock_initial_jepp` (Float) : stock au début de la simulation.
- `vecteur_production` (Array 1D) : profil de production prévu, facteur de charge entre 0.0 et 1.0 par jour.

Sorties :

- `jepp_restant` (Array 1D) : évolution journalière du stock.
- `date_epuisement` (Int) : index du jour où le stock atteint 0, si avant l'arrêt.

```python
# Implémentation via la somme cumulée (cumsum)
# Cumule l'énergie consommée jour après jour
jepp_consommes = np.cumsum(vecteur_production)

# Calcule le stock restant à chaque instant
jepp_restant = stock_initial_jepp - jepp_consommes

# Trouve le jour exact où le stock tombe sous 0
jours_epuises = np.where(jepp_restant <= 0)[0]
date_epuisement = jours_epuises[0] if len(jours_epuises) > 0 else None
```

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
# L'impact sur la date d'épuisement sera automatiquement recalculé par la règle A
```

### D. Stretch-out et reprise (contrainte physique automatique)

Principe : le backend force une baisse de puissance en fin de cycle si l'uranium manque pour atteindre la date d'arrêt à 100 %.

Entrées :

- `jepp_restant` (Array 1D) : stock calculé sans stretch-out.
- `date_arret_prevue` (Int) : jour fixé pour la maintenance.

Sorties :

- `vecteur_production_corrige` (Array 1D) : profil écrasé avec la puissance dégradée.

```python
# Si on constate que le réacteur tombe à zéro avant la date prévue
if date_epuisement and date_epuisement < date_arret_prevue:
    jours_a_couvrir = date_arret_prevue - date_epuisement
    # On force une baisse de puissance sur la fin de campagne pour faire tenir le stock
    vecteur_production[date_epuisement - jours_a_couvrir : date_arret_prevue] = puissance_degradee
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

Entrées : variation de puissance entre deux états de simulation (MW).

Sorties : alerte (Booléen).

Logique : si la différence absolue de puissance est supérieure à 100 MW, lever le flag `UMM_requise = True`.

### B. Contraintes du réseau haute tension (RTE)

Entrées : calendrier des arrêts programmés, données régionales des centrales.

Sorties : statut de validation du Gantt (Valide/Invalide).

Logique : empêcher le glissement d'un arrêt si cela engendre au moins 2 réacteurs arrêtés simultanément dans la même région, ou interdire l'enregistrement de l'arrêt s'il tombe entre décembre et février.

### C. Limites de compétences industrielles

Entrées : dates de début et de fin des arrêts de type ASR/VP/VD.

Sorties : nombre d'équipes mobilisées par jour et alertes de dépassement.

Logique : sommation du nombre d'arrêts en cours à un instant T. Si `arrêts_simultanés > capacité_equipes_edf`, renvoyer un conflit de ressources à l'interface.

## 3. Points à clarifier

- Stretch-out : la règle D calcule `jours_a_couvrir` puis utilise cet écart comme décalage de début de slice. L'intention métier est de dégrader la puissance sur les jours couverts par le déficit de stock. Confirmer la formule exacte et la valeur de `puissance_degradee` avant implémentation.
- Seuil REMIT : la règle 2.A mentionne 100 MW. Confirmer si le seuil porte sur la variation de puissance ou sur la capacité de la tranche.
- Modulation : confirmer la valeur par défaut de `puissance_modulation` lorsque l'utilisateur ne la fournit pas.
