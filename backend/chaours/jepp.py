from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from chaours.types import FloatArray, Maintenance


def simulate_stock_cycles(
    requested_factors: FloatArray,
    initial_jepp: float,
    maintenances: Sequence[Maintenance],
) -> tuple[FloatArray, FloatArray, tuple[int, ...]]:
    """Applique la limite physique du stock JEPP sur chaque cycle.

    ``requested_factors`` a la forme ``(horizon,)`` et exprime une
    consommation en JEPP par jour. Il inclut déjà la modulation manuelle.
    Les jours de maintenance sont forcés à ``0`` même si une valeur non nulle
    y figure.

    ``maintenances`` contient les arrêts d'une seule tranche. La séquence peut
    être non triée ; elle est triée par ``start_day``. Les fenêtres sont
    valides, sans chevauchement et dans l'horizon.

    Un cycle va de ``0`` ou du ``end_day`` de l'arrêt précédent jusqu'au
    ``start_day`` de l'arrêt suivant, ou jusqu'à la fin de l'horizon pour le
    dernier cycle. Chaque cycle repart de ``initial_jepp``. La production est
    nulle sur ``[start_day, end_day)`` et le stock y reste constant. Au
    ``end_day``, le stock est réinitialisé à ``initial_jepp`` avant la
    production du jour.

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
    if requested_factors.ndim != 1:
        raise ValueError("requested_factors doit être un tableau 1D")
    if initial_jepp < 0.0:
        raise ValueError("initial_jepp doit être positif ou nul")
    if np.any(requested_factors < 0.0):
        raise ValueError("requested_factors ne doit pas contenir de valeur négative")

    horizon = requested_factors.shape[0]
    actual = np.zeros(horizon, dtype=np.float64)
    remaining = np.zeros(horizon, dtype=np.float64)
    depletion_days: list[int] = []

    sorted_maintenances = sorted(maintenances, key=lambda maintenance: maintenance.start_day)

    stock = initial_jepp
    cycle_start = 0

    for maintenance in sorted_maintenances:
        stock = initial_jepp
        deficit_started = False
        for day in range(cycle_start, maintenance.start_day):
            requested = requested_factors[day]
            if deficit_started:
                actual[day] = 0.0
            elif requested <= stock:
                actual[day] = requested
                stock -= requested
            else:
                actual[day] = stock
                stock = 0.0
                deficit_started = True
                depletion_days.append(day)
            remaining[day] = stock

        for day in range(maintenance.start_day, maintenance.end_day):
            actual[day] = 0.0
            remaining[day] = stock

        stock = initial_jepp
        cycle_start = maintenance.end_day

    stock = initial_jepp
    deficit_started = False
    for day in range(cycle_start, horizon):
        requested = requested_factors[day]
        if deficit_started:
            actual[day] = 0.0
        elif requested <= stock:
            actual[day] = requested
            stock -= requested
        else:
            actual[day] = stock
            stock = 0.0
            deficit_started = True
            depletion_days.append(day)
        remaining[day] = stock

    return actual, remaining, tuple(depletion_days)
