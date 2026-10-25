from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from chaours.constants import REMIT_THRESHOLD_MW
from chaours.types import (
    Alert,
    AlertKind,
    FloatArray,
    IntArray,
    Maintenance,
    Plant,
    PlantResult,
    Severity,
)


def neutronic_alerts(
    plant_results: Sequence[PlantResult],
    maintenances_by_plant: Mapping[str, Sequence[Maintenance]],
) -> list[Alert]:
    """Signale les tranches dont le stock est épuisé avant l'arrêt prévu.

    Parcourt les tranches dans l'ordre reçu. Pour chaque jour de
    ``PlantResult.depletion_days``, cherche le prochain ``start_day`` d'arrêt
    strictement supérieur à ce jour pour la même tranche. Renvoie une alerte
    ``NEUTRONIC_ANOMALY`` par jour de déplétion, de gravité ``CRITICAL``. Le
    message d'alerte demande une modulation manuelle. Il cite le
    jour de début du prochain arrêt, ou indique qu'aucun arrêt n'est prévu.
    """
    alerts: list[Alert] = []

    for result in plant_results:
        stop_starts = sorted(
            maintenance.start_day
            for maintenance in maintenances_by_plant.get(result.plant_id, ())
        )

        for day in result.depletion_days:
            next_stop = next(
                (start for start in stop_starts if start > day),
                None,
            )
            if next_stop is None:
                message = (
                    f"Stock JEPP épuisé le jour {day} pour la tranche "
                    f"{result.plant_id} : aucun arrêt n'est planifié. "
                    "Appliquez une modulation manuelle."
                )
            else:
                message = (
                    f"Stock JEPP épuisé le jour {day} pour la tranche "
                    f"{result.plant_id} : prochain arrêt au jour {next_stop}. "
                    "Appliquez une modulation manuelle."
                )

            alerts.append(
                Alert(
                    kind=AlertKind.NEUTRONIC_ANOMALY,
                    day=day,
                    plant_id=result.plant_id,
                    message=message,
                    severity=Severity.CRITICAL,
                )
            )

    return alerts


def remit_alerts(
    variation_mw: FloatArray,
    plant_ids: Sequence[str],
    threshold_mw: float = REMIT_THRESHOLD_MW,
) -> list[Alert]:
    """Signale les variations de puissance au-dessus du seuil REMIT.

    ``variation_mw`` a la forme ``(n_plants, horizon - 1)`` et ``plant_ids``
    a la longueur ``n_plants``. Renvoie une alerte ``REMIT_UMM`` par tranche
    et par jour où ``abs(variation_mw[plant_index, day_index]) >
    threshold_mw``. Le jour de l'alerte vaut ``day_index + 1``, soit le
    second jour de la différence. L'alerte porte l'identifiant de la
    tranche, une gravité ``WARNING``, et inclut les bornes des arrêts
    planifiés.
    """
    if variation_mw.ndim != 2:
        raise ValueError(
            f"variation_mw must be two-dimensional, got {variation_mw.ndim} dimensions"
        )
    if variation_mw.shape[0] != len(plant_ids):
        raise ValueError(
            "variation_mw rows must match plant ids: "
            f"{variation_mw.shape[0]} != {len(plant_ids)}"
        )

    alerts: list[Alert] = []

    for plant_index, plant_id in enumerate(plant_ids):
        day_indices = np.flatnonzero(np.abs(variation_mw[plant_index]) > threshold_mw)
        for day_index in day_indices:
            day = int(day_index) + 1
            variation = float(variation_mw[plant_index, day_index])
            alerts.append(
                Alert(
                    kind=AlertKind.REMIT_UMM,
                    day=day,
                    plant_id=plant_id,
                    message=(
                        f"Variation de puissance REMIT pour la tranche "
                        f"{plant_id} au jour {day} : "
                        f"{variation:+.2f} MW (seuil {threshold_mw:.2f} MW)."
                    ),
                    severity=Severity.WARNING,
                )
            )

    return alerts


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
    if deficit_day_indices.ndim != 1:
        raise ValueError(
            "deficit_day_indices must be one-dimensional, "
            f"got {deficit_day_indices.ndim} dimensions"
        )

    alerts: list[Alert] = []
    for day_index in deficit_day_indices:
        day = int(day_index)
        alerts.append(
            Alert(
                kind=AlertKind.RTE_DEFICIT,
                day=day,
                plant_id=None,
                message=(
                    f"Déficit national au jour {day} : "
                    "l'offre est inférieure à la demande."
                ),
                severity=Severity.CRITICAL,
            )
        )

    return alerts
