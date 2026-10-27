import numpy as np

from core.engine.production import (
    apply_maintenance,
    apply_manual_modulation,
    maintenance_mask,
)
from core.models import Arret, Modulation, TypeArret


def test_maintenance_mask_marks_all_outage_days():
    mask = maintenance_mask(
        (
            Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3),
            Arret(type_arret=TypeArret.VP, jour_debut=4, jour_fin=6),
        ),
        6,
    )

    assert mask.shape == (6,)
    assert mask.dtype == np.bool_
    assert mask.tolist() == [False, True, True, False, True, True]


def test_maintenance_mask_excludes_last_day():
    mask = maintenance_mask(
        (Arret(type_arret=TypeArret.ASR, jour_debut=2, jour_fin=4),),
        5,
    )

    assert mask.tolist() == [False, False, True, True, False]


def test_maintenance_mask_is_empty_without_arrets():
    mask = maintenance_mask((), 3)

    assert mask.tolist() == [False, False, False]


def test_manual_modulation_applies_only_inside_window():
    factors = np.ones(5)

    result = apply_manual_modulation(
        factors,
        (Modulation(jour_debut=1, jour_fin=3, facteur=0.4),),
    )

    assert result.tolist() == [1.0, 0.4, 0.4, 1.0, 1.0]


def test_manual_modulation_handles_multiple_windows():
    factors = np.ones(7)

    result = apply_manual_modulation(
        factors,
        (
            Modulation(jour_debut=1, jour_fin=4, facteur=0.5),
            Modulation(jour_debut=4, jour_fin=6, facteur=0.2),
        ),
    )

    assert result.tolist() == [1.0, 0.5, 0.5, 0.5, 0.2, 0.2, 1.0]


def test_apply_maintenance_zeros_only_outage_days():
    factors = np.array([0.9, 0.8, 0.7, 0.6])
    mask = np.array([False, True, False, True])

    result = apply_maintenance(factors, mask)

    assert result.tolist() == [0.9, 0.0, 0.7, 0.0]


def test_maintenance_wins_when_applied_after_modulation():
    factors = np.ones(4)
    mask = maintenance_mask(
        (Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3),),
        4,
    )

    modulated = apply_manual_modulation(
        factors,
        (Modulation(jour_debut=1, jour_fin=4, facteur=0.5),),
    )
    result = apply_maintenance(modulated, mask)

    assert result.tolist() == [1.0, 0.0, 0.0, 0.5]


def test_functions_return_new_arrays_without_mutating_inputs():
    factors = np.ones(4)
    factors_before = factors.copy()
    mask = np.zeros(4, dtype=np.bool_)
    mask_before = mask.copy()

    modulated = apply_manual_modulation(
        factors,
        (Modulation(jour_debut=0, jour_fin=2, facteur=0.3),),
    )
    maintained = apply_maintenance(modulated, mask)
    assert not np.shares_memory(modulated, factors)
    assert not np.shares_memory(maintained, modulated)
    assert not np.shares_memory(maintained, mask)
    assert np.array_equal(factors, factors_before)
    assert np.array_equal(mask, mask_before)
