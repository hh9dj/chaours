from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from chaours.types import BoolArray, FloatArray, Maintenance, Modulation


def maintenance_mask(
    maintenances: Sequence[Maintenance],
    horizon: int,
) -> BoolArray:
    """Construit le masque des arrêts d'une tranche.

    Renvoie un tableau booléen de forme ``(horizon,)``. Une cellule ``True``
    marque un jour où la tranche est arrêtée.
    """
    mask = np.zeros(horizon, dtype=np.bool_)

    for maintenance in maintenances:
        mask[maintenance.start_day : maintenance.end_day] = True

    return mask


def modulation_factors(horizon: int) -> FloatArray:
    """Construit le vecteur de facteurs de charge nominaux.

    Renvoie un tableau ``float64`` de forme ``(horizon,)`` rempli de ``1.0``.
    """
    return np.ones(horizon, dtype=np.float64)


def apply_manual_modulation(
    factors: FloatArray,
    modulations: Sequence[Modulation],
) -> FloatArray:
    """Applique les fenêtres de modulation de l'utilisateur.

    Chaque fenêtre force ``factor`` sur l'intervalle de jours semi-ouvert
    ``[start_day, end_day)``. ``factors`` a la forme ``(horizon,)`` et
    appartient à une seule tranche. Renvoie un nouveau tableau de même forme.
    """
    result = factors.copy()

    for modulation in modulations:
        result[modulation.start_day : modulation.end_day] = modulation.factor

    return result


def apply_maintenance(factors: FloatArray, mask: BoolArray) -> FloatArray:
    """Force la production à ``0.0`` sur chaque jour d'arrêt.

    ``mask`` a la même forme que ``factors``. La maintenance a la priorité
    la plus haute dans le pipeline. Renvoie un nouveau tableau.
    """
    result = factors.copy()
    result[mask] = 0.0
    return result
