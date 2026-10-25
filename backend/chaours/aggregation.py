from __future__ import annotations

import numpy as np

from chaours.types import FloatArray, IntArray


def energy_mwh(factors: FloatArray, nominal_power_mw: FloatArray) -> FloatArray:
    """Convertit les facteurs de charge en énergie journalière.

    ``factors`` a la forme ``(n_plants, horizon)`` et ``nominal_power_mw``
    la forme ``(n_plants,)``. Renvoie un tableau ``float64`` de forme
    ``(n_plants, horizon)`` en MWh/jour : ``factor * nominal_power_mw * 24``.
    """
    if factors.ndim != 2:
        raise ValueError(
            f"factors must be two-dimensional, got {factors.ndim} dimensions"
        )
    if nominal_power_mw.ndim != 1:
        raise ValueError(
            "nominal_power_mw must be one-dimensional, "
            f"got {nominal_power_mw.ndim} dimensions"
        )
    if factors.shape[0] != nominal_power_mw.shape[0]:
        raise ValueError(
            "nominal power length must match plant axis: "
            f"{nominal_power_mw.shape[0]} != {factors.shape[0]}"
        )

    result = factors * nominal_power_mw[:, None] * 24.0
    return result.astype(np.float64, copy=False)


def national_supply(energy_mwh: FloatArray) -> FloatArray:
    """Somme l'énergie des tranches sur l'axe des tranches.

    ``energy_mwh`` a la forme ``(n_plants, horizon)``. Renvoie un tableau 1D
    de forme ``(horizon,)`` en MWh/jour.
    """
    if energy_mwh.ndim != 2:
        raise ValueError(
            "energy_mwh must be two-dimensional, "
            f"got {energy_mwh.ndim} dimensions"
        )

    result = np.sum(energy_mwh, axis=0)
    return result.astype(np.float64, copy=False)


def deficit_days(supply_mwh: FloatArray, demand_mwh: FloatArray) -> IntArray:
    """Renvoie les indices des jours où l'offre est inférieure à la demande.

    Les deux tableaux ont la forme ``(horizon,)``. Renvoie un tableau
    d'indices entiers, vide quand l'offre couvre toujours la demande.
    """
    if supply_mwh.ndim != 1 or demand_mwh.ndim != 1:
        raise ValueError("supply_mwh and demand_mwh must be one-dimensional")
    if supply_mwh.shape != demand_mwh.shape:
        raise ValueError(
            "supply_mwh and demand_mwh must have the same shape: "
            f"{supply_mwh.shape} != {demand_mwh.shape}"
        )

    return np.flatnonzero(supply_mwh < demand_mwh)


def daily_power_variation_mw(energy_mwh: FloatArray) -> FloatArray:
    """Calcule la variation de puissance moyenne d'un jour à l'autre.

    ``energy_mwh`` a la forme ``(n_plants, horizon)`` ou ``(horizon,)``.
    Convertit les MWh/jour en MW moyens (division par 24) avant d'appliquer
    ``np.diff`` sur le dernier axe. Renvoie un tableau plus court d'un jour.
    """
    if energy_mwh.ndim not in (1, 2):
        raise ValueError(
            "energy_mwh must be one- or two-dimensional, "
            f"got {energy_mwh.ndim} dimensions"
        )

    average_power_mw = energy_mwh / 24.0
    return np.diff(average_power_mw, axis=-1)
