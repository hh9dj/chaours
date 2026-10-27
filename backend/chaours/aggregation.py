import numpy as np

from chaours.types import FloatArray, IntArray


def energy_mwh(factors: FloatArray, nominal_power_mw: FloatArray) -> FloatArray:
    """Convertit les facteurs de charge en énergie journalière.

    ``factors`` a la forme ``(n_plants, horizon)`` et ``nominal_power_mw``
    la forme ``(n_plants,)``. Renvoie un tableau ``float64`` de forme
    ``(n_plants, horizon)`` en MWh/jour : ``factor * nominal_power_mw * 24``.
    """
    result = factors * nominal_power_mw[:, None] * 24.0
    return result.astype(np.float64, copy=False)


def national_supply(energy_mwh: FloatArray) -> FloatArray:
    """Somme l'énergie des tranches sur l'axe des tranches.

    ``energy_mwh`` a la forme ``(n_plants, horizon)``. Renvoie un tableau 1D
    de forme ``(horizon,)`` en MWh/jour.
    """
    result = np.sum(energy_mwh, axis=0)
    return result.astype(np.float64, copy=False)


def deficit_days(supply_mwh: FloatArray, demand_mwh: FloatArray) -> IntArray:
    """Renvoie les indices des jours où l'offre est inférieure à la demande.

    Les deux tableaux ont la forme ``(horizon,)``. Renvoie un tableau
    d'indices entiers, vide quand l'offre couvre toujours la demande.
    """
    return np.flatnonzero(supply_mwh < demand_mwh)


def daily_power_variation_mw(energy_mwh: FloatArray) -> FloatArray:
    """Calcule la variation de puissance moyenne d'un jour à l'autre.

    ``energy_mwh`` a la forme ``(n_plants, horizon)`` ou ``(horizon,)``.
    Convertit les MWh/jour en MW moyens (division par 24) avant d'appliquer
    ``np.diff`` sur le dernier axe. Renvoie un tableau plus court d'un jour.
    """
    average_power_mw = energy_mwh / 24.0
    return np.diff(average_power_mw, axis=-1)
