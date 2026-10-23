from __future__ import annotations

import numpy as np


def remaining_jepp(initial_stock: float, factors: np.ndarray) -> np.ndarray:
    """Calcule le stock de combustible restant chaque jour.

    ``factors`` est un vecteur 1D de facteurs de charge de forme
    ``(horizon,)``. Renvoie un tableau ``float64`` de forme ``(horizon,)``
    où chaque valeur vaut ``initial_stock - np.cumsum(factors)``.
    """
    return initial_stock - np.cumsum(factors)


def depletion_day(remaining_jepp: np.ndarray) -> int | None:
    """Renvoie le premier jour où le stock restant est ``<= 0``.

    Renvoie ``None`` quand le stock n'est jamais épuisé sur l'horizon.
    """
    day = np.where(remaining_jepp <= 0)
    return day[0][0] if day[0].size else None


def stretch_out(
    factors: np.ndarray,
    initial_stock: float,
    outage_start: int,
) -> tuple[np.ndarray, bool]:
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
