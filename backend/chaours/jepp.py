from __future__ import annotations

from collections.abc import Sequence

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

    ``maintenances`` contient les arrêts d'une seule tranche, triés par
    ``start_day``. Les fenêtres sont valides, sans chevauchement et dans
    l'horizon.

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
    raise NotImplementedError
