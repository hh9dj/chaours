import numpy as np

from chaours.production import (
    apply_maintenance,
    apply_manual_modulation,
    maintenance_mask,
    modulation_factors,
)
from chaours.types import Maintenance, Modulation, OutageKind


def test_nominal_factors_are_all_ones():
    factors = modulation_factors(4)

    assert factors.shape == (4,)
    assert factors.dtype == np.float64
    assert np.array_equal(factors, np.ones(4))


def test_maintenance_mask_marks_all_outage_days():
    mask = maintenance_mask(
        (
            Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3),
            Maintenance(kind=OutageKind.VP, start_day=4, end_day=6),
        ),
        6,
    )

    assert mask.shape == (6,)
    assert mask.dtype == np.bool_
    assert mask.tolist() == [False, True, True, False, True, True]


def test_maintenance_mask_excludes_last_day():
    mask = maintenance_mask(
        (Maintenance(kind=OutageKind.ASR, start_day=2, end_day=4),),
        5,
    )

    assert mask.tolist() == [False, False, True, True, False]


def test_maintenance_mask_is_empty_without_maintenances():
    mask = maintenance_mask((), 3)

    assert mask.tolist() == [False, False, False]


def test_manual_modulation_applies_only_inside_window():
    factors = np.ones(5)

    result = apply_manual_modulation(
        factors,
        (Modulation(start_day=1, end_day=3, factor=0.4),),
    )

    assert result.tolist() == [1.0, 0.4, 0.4, 1.0, 1.0]


def test_manual_modulation_handles_multiple_and_overlapping_windows():
    factors = np.ones(7)

    result = apply_manual_modulation(
        factors,
        (
            Modulation(start_day=1, end_day=4, factor=0.5),
            Modulation(start_day=3, end_day=6, factor=0.2),
        ),
    )

    assert result.tolist() == [1.0, 0.5, 0.5, 0.2, 0.2, 0.2, 1.0]


def test_apply_maintenance_zeros_only_outage_days():
    factors = np.array([0.9, 0.8, 0.7, 0.6])
    mask = np.array([False, True, False, True])

    result = apply_maintenance(factors, mask)

    assert result.tolist() == [0.9, 0.0, 0.7, 0.0]


def test_maintenance_wins_when_applied_after_modulation():
    factors = np.ones(4)
    mask = maintenance_mask(
        (Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3),),
        4,
    )

    modulated = apply_manual_modulation(
        factors,
        (Modulation(start_day=1, end_day=4, factor=0.5),),
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
        (Modulation(start_day=0, end_day=2, factor=0.3),),
    )
    maintained = apply_maintenance(modulated, mask)
    nominal = modulation_factors(4)
    nominal[0] = 0.5
    other_nominal = modulation_factors(4)

    assert not np.shares_memory(modulated, factors)
    assert not np.shares_memory(maintained, modulated)
    assert not np.shares_memory(maintained, mask)
    assert np.array_equal(factors, factors_before)
    assert np.array_equal(mask, mask_before)
    assert np.array_equal(other_nominal, np.ones(4))
