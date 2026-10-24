from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from chaours.constants import REMIT_THRESHOLD_MW
from chaours.types import (
    Alert,
    AlertKind,
    FloatArray,
    IntArray,
    Plant,
    PlantResult,
    Severity,
)


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
    variation_mw: FloatArray,
    threshold_mw: float = REMIT_THRESHOLD_MW,
) -> list[Alert]:
    """Signale les variations de puissance au-dessus du seuil REMIT.

    ``variation_mw`` est un tableau 1D de forme ``(horizon - 1,)``. Renvoie
    une alerte ``REMIT_UMM`` par jour où ``abs(variation_mw) > threshold_mw``.
    """
    raise NotImplementedError


def spot_below_usage_value_alerts(
    spot_prices: FloatArray,
    plants: Sequence[Plant],
    usage_values_eur_mwh: Mapping[str, float],
) -> list[Alert]:
    """Signale les jours où le prix spot est inférieur à la valeur d'usage.

    ``spot_prices`` a la forme ``(horizon,)``. ``usage_values_eur_mwh`` est
    indexé par identifiant de tranche et contient un scalaire statique par
    tranche dans le MVP, pas une série journalière. Renvoie une alerte
    ``SPOT_BELOW_USAGE_VALUE`` par couple tranche/jour concerné. La production
    n'est pas modifiée.
    """
    alerts: list[Alert] = []
    for plant in plants:
        usage_value = usage_values_eur_mwh[plant.id]
        for day in np.where(spot_prices < usage_value)[0]:
            alerts.append(
                Alert(
                    kind=AlertKind.SPOT_BELOW_USAGE_VALUE,
                    day=int(day),
                    plant_id=plant.id,
                    message=(
                        "Prix spot inférieur à la valeur d'usage : "
                        f"{spot_prices[day]:.2f} €/MWh < {usage_value:.2f} €/MWh."
                    ),
                    severity=Severity.WARNING,
                )
            )
    return alerts


def deficit_alerts(deficit_day_indices: IntArray) -> list[Alert]:
    """Signale les jours où l'offre nationale est inférieure à la demande.

    ``deficit_day_indices`` est un tableau 1D d'indices entiers. Renvoie une
    alerte ``RTE_DEFICIT`` par jour.
    """
    raise NotImplementedError
