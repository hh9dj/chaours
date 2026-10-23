from __future__ import annotations

import numpy as np


def energy_mwh(factors: np.ndarray, nominal_power_mw: np.ndarray) -> np.ndarray:
    """Convertit les facteurs de charge en énergie journalière.

    ``factors`` a la forme ``(n_plants, horizon)`` et ``nominal_power_mw``
    la forme ``(n_plants,)``. Renvoie un tableau ``float64`` de forme
    ``(n_plants, horizon)`` en MWh/jour : ``factor * nominal_power_mw * 24``.
    """
    raise NotImplementedError


def national_supply(energy_mwh: np.ndarray) -> np.ndarray:
    """Somme l'énergie des tranches sur l'axe des tranches.

    ``energy_mwh`` a la forme ``(n_plants, horizon)``. Renvoie un tableau 1D
    de forme ``(horizon,)`` en MWh/jour.
    """
    raise NotImplementedError


def deficit_days(supply_mwh: np.ndarray, demand_mwh: np.ndarray) -> np.ndarray:
    """Renvoie les indices des jours où l'offre est inférieure à la demande.

    Les deux tableaux ont la forme ``(horizon,)``. Renvoie un tableau
    d'indices entiers, vide quand l'offre couvre toujours la demande.
    """
    raise NotImplementedError


def daily_power_variation_mw(energy_mwh: np.ndarray) -> np.ndarray:
    """Calcule la variation de puissance moyenne d'un jour à l'autre.

    ``energy_mwh`` a la forme ``(n_plants, horizon)`` ou ``(horizon,)``.
    Convertit les MWh/jour en MW moyens (division par 24) avant d'appliquer
    ``np.diff`` sur le dernier axe. Renvoie un tableau plus court d'un jour.
    """
    raise NotImplementedError
