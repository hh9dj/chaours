from collections.abc import Sequence

import numpy as np

from chaours.types import Arret, FloatArray


# TODO: remove private functions
# return types as dataclass
def _consume_cycle(
    requested_factors: FloatArray,
    start_day: int,
    end_day: int,
    initial_jepp: float,
) -> tuple[FloatArray, FloatArray, int | None]:
    """Consomme un cycle ``[start_day, end_day)`` avec un stock initial donné.

    Renvoie les facteurs réels du cycle, le stock en fin de journée et le
    premier jour en déficit, ou ``None`` si le stock suffit.
    """
    requested = requested_factors[start_day:end_day]
    actual = requested.copy()
    cumulative = np.cumsum(requested)
    deficit_indices = np.flatnonzero(cumulative > initial_jepp)

    if deficit_indices.size == 0:
        remaining = initial_jepp - cumulative
        return actual, remaining, None

    deficit_offset = int(deficit_indices[0])
    depletion_day = start_day + deficit_offset
    if deficit_offset == 0:
        available = initial_jepp
    else:
        available = initial_jepp - cumulative[deficit_offset - 1]

    actual[deficit_offset] = available
    actual[deficit_offset + 1 :] = 0.0
    remaining = np.zeros_like(cumulative)
    remaining[:deficit_offset] = initial_jepp - cumulative[:deficit_offset]

    return actual, remaining, depletion_day


def simulate_stock_cycles(
    requested_factors: FloatArray,
    initial_jepp: float,
    arrets: Sequence[Arret],
) -> tuple[FloatArray, FloatArray, tuple[int, ...]]:
    """Applique la limite physique du stock JEPP sur chaque cycle.

    ``requested_factors`` a la forme ``(horizon,)`` et exprime une
    consommation en JEPP par jour. Il inclut déjà la modulation manuelle et
    les jours de maintenance y sont déjà mis à ``0.0`` par le pipeline de
    production. JEPP ne masque pas lui-même les jours d'arrêt.

    ``arrets`` contient les arrêts d'une seule tranche. La séquence peut
    être non triée ; elle est triée par ``start_day``. Les fenêtres sont
    valides, sans chevauchement et dans l'horizon. Les arrêts servent
    uniquement à découper les cycles et à réinitialiser le stock au
    ``jour_fin``.

    Un cycle va de ``0`` ou du ``jour_fin`` de l'arrêt précédent jusqu'au
    ``jour_fin`` de l'arrêt courant, jours d'arrêt inclus, ou jusqu'à la fin
    de l'horizon pour le dernier cycle. Comme les facteurs demandés y sont
    déjà nuls, le stock reste constant pendant l'arrêt. Chaque cycle repart
    de ``initial_jepp`` ; le rechargement est appliqué au ``jour_fin`` avant
    la production de ce jour.

    Si la consommation demandée d'un cycle dépasse ``initial_jepp``, le
    premier jour en déficit est le premier jour qui ne peut pas être servi
    entièrement. Ce jour-là, la production réelle vaut le stock restant.
    Ensuite, la production réelle vaut ``0`` jusqu'au rechargement suivant.
    Une consommation cumulée exactement égale à ``initial_jepp`` en fin de
    cycle n'est pas un déficit.

    Renvoie ``(actual_factors, remaining_jepp, depletion_days)``.
    ``remaining_jepp`` est le stock en fin de journée, borné à ``0``.
    ``depletion_days`` contient le premier jour en déficit de chaque cycle
    concerné, par ordre croissant. Aucune dégradation automatique ni
    stretch-out n'est appliqué au-delà de la limite physique du stock.
    """
    horizon = requested_factors.shape[0]
    actual = np.zeros(horizon, dtype=np.float64)
    remaining = np.zeros(horizon, dtype=np.float64)
    depletion_days: list[int] = []

    sorted_arrets = sorted(arrets, key=lambda arret: arret.jour_debut)

    cycle_start = 0
    for arret in sorted_arrets:
        cycle_actual, cycle_remaining, depletion_day = _consume_cycle(
            requested_factors,
            cycle_start,
            arret.jour_fin,
            initial_jepp,
        )
        actual[cycle_start : arret.jour_fin] = cycle_actual
        remaining[cycle_start : arret.jour_fin] = cycle_remaining
        if depletion_day is not None:
            depletion_days.append(depletion_day)
        cycle_start = arret.jour_fin

    cycle_actual, cycle_remaining, depletion_day = _consume_cycle(
        requested_factors,
        cycle_start,
        horizon,
        initial_jepp,
    )
    actual[cycle_start:horizon] = cycle_actual
    remaining[cycle_start:horizon] = cycle_remaining
    if depletion_day is not None:
        depletion_days.append(depletion_day)

    return actual, remaining, tuple(depletion_days)
