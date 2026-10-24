from __future__ import annotations

import numpy as np

from chaours.types import FloatArray


def remaining_jepp(initial_stock: float, factors: FloatArray) -> FloatArray:
    """Calcule le stock de combustible restant chaque jour.

    ``factors`` est un vecteur 1D de facteurs de charge de forme
    ``(horizon,)``. Renvoie un tableau ``float64`` de forme ``(horizon,)``
    où chaque valeur vaut ``initial_stock - np.cumsum(factors)``.
    """
    return initial_stock - np.cumsum(factors)


def depletion_day(remaining_jepp: FloatArray) -> int | None:
    """Renvoie le premier jour où le stock restant est ``<= 0``.

    Renvoie ``None`` quand le stock n'est jamais épuisé sur l'horizon.
    """
    days = np.flatnonzero(remaining_jepp <= 0)
    return int(days[0]) if days.size else None


def stretch_out(
    factors: FloatArray,
    initial_stock: float,
    outage_start: int,
) -> tuple[FloatArray, bool]:
    """Dégrade la production pour que le stock tienne jusqu'à l'arrêt prévu.

    Si l'épuisement survient avant ``outage_start``, les facteurs de charge
    sur ``[0, outage_start)`` sont mis à l'échelle pour que la consommation
    cumulée égale ``initial_stock``. L'énergie est conservée et la forme du
    profil de production est préservée.

    Renvoie le tableau de facteurs de charge corrigé et un indicateur à
    ``True`` quand le stretch-out a été appliqué. L'indicateur vaut ``False``
    quand aucune correction n'est nécessaire.
    """
    raise NotImplementedError
