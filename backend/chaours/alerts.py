from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from .constants import REMIT_THRESHOLD_MW
from .types import Alert, PlantResult


def neutronic_alerts(
    plant_results: Sequence[PlantResult],
    outage_starts: Mapping[str, int],
) -> list[Alert]:
    """Signale les tranches dont le stock est épuisé avant l'arrêt prévu.

    Compare ``PlantResult.depletion_day`` à ``outage_starts``.
    Renvoie une alerte ``NEUTRONIC_ANOMALY`` par tranche concernée.
    """
    raise NotImplementedError


def remit_alerts(
    variation_mw: np.ndarray,
    threshold_mw: float = REMIT_THRESHOLD_MW,
) -> list[Alert]:
    """Signale les variations de puissance au-dessus du seuil REMIT.

    ``variation_mw`` est un tableau 1D de forme ``(horizon - 1,)``. Renvoie
    une alerte ``REMIT_UMM`` par jour où ``abs(variation_mw) > threshold_mw``.
    """
    raise NotImplementedError


def deficit_alerts(deficit_day_indices: np.ndarray) -> list[Alert]:
    """Signale les jours où l'offre nationale est inférieure à la demande.

    ``deficit_day_indices`` est un tableau 1D d'indices entiers. Renvoie une
    alerte ``RTE_DEFICIT`` par jour.
    """
    raise NotImplementedError
