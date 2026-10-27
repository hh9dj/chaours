from collections.abc import Mapping, Sequence

import numpy as np

from chaours.constants import REMIT_THRESHOLD_MW
from chaours.types import (
    Alerte,
    Arret,
    FloatArray,
    IntArray,
    ResultatTranche,
    TypeAlerte,
)


def neutronic_alerts(
    resultats: Sequence[ResultatTranche],
    arrets_par_tranche: Mapping[str, Sequence[Arret]],
) -> list[Alerte]:
    """Signale les tranches dont le stock est épuisé avant l'arrêt prévu.

    Parcourt les tranches dans l'ordre reçu. Pour chaque jour de
    ``ResultatTranche.jours_epuisement``, cherche le prochain
    ``jour_debut`` d'arrêt strictement supérieur à ce jour pour la même
    tranche. Renvoie une alerte ``NEUTRONIC_ANOMALY`` par jour de déplétion,
    Le message demande une modulation manuelle.
    """
    alerts: list[Alerte] = []

    for resultat in resultats:
        stop_starts = sorted(
            arret.jour_debut
            for arret in arrets_par_tranche.get(resultat.tranche_id, ())
        )

        for day in resultat.jours_epuisement:
            next_stop = next(
                (start for start in stop_starts if start > day),
                None,
            )
            if next_stop is None:
                message = (
                    f"Stock JEPP épuisé le jour {day} pour la tranche "
                    f"{resultat.tranche_id} : aucun arrêt n'est planifié. "
                    "Appliquez une modulation manuelle."
                )
            else:
                message = (
                    f"Stock JEPP épuisé le jour {day} pour la tranche "
                    f"{resultat.tranche_id} : prochain arrêt au jour "
                    f"{next_stop}. Appliquez une modulation manuelle."
                )

            alerts.append(
                Alerte(
                    type_alerte=TypeAlerte.NEUTRONIC_ANOMALY,
                    jour=day,
                    tranche_id=resultat.tranche_id,
                    message=message,
                )
            )

    return alerts


def remit_alerts(
    variation_mw: FloatArray,
    tranche_ids: Sequence[str],
    threshold_mw: float = REMIT_THRESHOLD_MW,
) -> list[Alerte]:
    """Signale les variations de puissance au-dessus du seuil REMIT.

    ``variation_mw`` a la forme ``(n_tranches, horizon - 1)`` et
    ``tranche_ids`` a la longueur ``n_tranches``. Renvoie une alerte
    ``REMIT_UMM`` par tranche et par jour où la variation absolue dépasse
    ``threshold_mw``. Le jour de l'alerte vaut ``day_index + 1``.
    """
    alerts: list[Alerte] = []

    for index, tranche_id in enumerate(tranche_ids):
        day_indices = np.flatnonzero(
            np.abs(variation_mw[index]) > threshold_mw
        )
        for day_index in day_indices:
            day = int(day_index) + 1
            variation = float(variation_mw[index, day_index])
            alerts.append(
                Alerte(
                    type_alerte=TypeAlerte.REMIT_UMM,
                    jour=day,
                    tranche_id=tranche_id,
                    message=(
                        f"Variation de puissance REMIT pour la tranche "
                        f"{tranche_id} au jour {day} : "
                        f"{variation:+.2f} MW (seuil {threshold_mw:.2f} MW)."
                    ),
                )
            )

    return alerts


def spot_below_usage_value_alerts(
    prix_spot_eur_mwh: FloatArray,
    valeur_usage_eur_mwh: FloatArray,
) -> list[Alerte]:
    """Signale les jours où le prix spot est inférieur à la valeur d'usage.

    Les deux séries ont la forme ``(horizon,)``. Renvoie une alerte nationale
    ``SPOT_BELOW_USAGE_VALUE`` par jour concerné. La production n'est pas
    modifiée.
    """
    alerts: list[Alerte] = []
    for day in np.where(prix_spot_eur_mwh < valeur_usage_eur_mwh)[0]:
        spot = float(prix_spot_eur_mwh[day])
        usage_value = float(valeur_usage_eur_mwh[day])
        alerts.append(
            Alerte(
                type_alerte=TypeAlerte.SPOT_BELOW_USAGE_VALUE,
                jour=int(day),
                tranche_id=None,
                message=(
                    "Prix spot inférieur à la valeur d'usage : "
                    f"{spot:.2f} €/MWh < {usage_value:.2f} €/MWh."
                ),
            )
        )
    return alerts


def deficit_alerts(deficit_day_indices: IntArray) -> list[Alerte]:
    """Signale les jours où l'offre nationale est inférieure à la demande.

    ``deficit_day_indices`` est un tableau 1D d'indices entiers. Renvoie une
    alerte nationale ``RTE_DEFICIT`` par jour.
    """
    alerts: list[Alerte] = []
    for day_index in deficit_day_indices:
        day = int(day_index)
        alerts.append(
            Alerte(
                type_alerte=TypeAlerte.RTE_DEFICIT,
                jour=day,
                tranche_id=None,
                message=(
                    f"Déficit national au jour {day} : "
                    "l'offre est inférieure à la demande."
                ),
            )
        )

    return alerts
