import numpy as np
import pytest

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


def test_maintenance_mask_marks_outage_days_for_several_plants():
    mask = maintenance_mask(
        (
            Maintenance("P1", OutageKind.ASR, 1, 3),
            Maintenance("P2", OutageKind.ASR, 0, 1),
            Maintenance("P2", OutageKind.ASR, 4, 6),
        ),
        ("P1", "P2"),
        6,
    )

    assert mask.shape == (2, 6)
    assert mask.dtype == np.bool_
    assert mask[0].tolist() == [False, True, True, False, False, False]
    assert mask[1].tolist() == [True, False, False, False, True, True]


def test_maintenance_mask_respects_semi_open_end_day():
    mask = maintenance_mask(
        (Maintenance("P1", OutageKind.ASR, 2, 4),),
        ("P1",),
        5,
    )

    assert mask.tolist() == [[False, False, True, True, False]]


def test_maintenance_mask_matches_plants_by_id_not_order():
    mask = maintenance_mask(
        (Maintenance("P2", OutageKind.ASR, 1, 3),),
        ("P1", "P2"),
        4,
    )

    assert mask.tolist() == [
        [False, False, False, False],
        [False, True, True, False],
    ]


def test_maintenance_mask_is_empty_without_maintenances():
    mask = maintenance_mask((), ("P1", "P2"), 3)

    assert mask.tolist() == [
        [False, False, False],
        [False, False, False],
    ]


@pytest.mark.parametrize(
    "maintenance",
    [
        Maintenance("UNKNOWN", OutageKind.ASR, 0, 1),
        Maintenance("P1", OutageKind.ASR, -1, 1),
        Maintenance("P1", OutageKind.ASR, 0, 5),
        Maintenance("P1", OutageKind.ASR, 2, 2),
        Maintenance("P1", OutageKind.ASR, 3, 2),
    ],
)
def test_maintenance_mask_rejects_invalid_input(maintenance):
    with pytest.raises(ValueError):
        maintenance_mask((maintenance,), ("P1",), 4)


def test_maintenance_mask_rejects_non_positive_horizon():
    with pytest.raises(ValueError):
        maintenance_mask((), ("P1",), 0)


def test_manual_modulation_applies_only_inside_window_and_to_correct_plant():
    factors = np.ones((2, 5))

    result = apply_manual_modulation(
        factors,
        (Modulation("P2", 1, 3, 0.4),),
        ("P1", "P2"),
    )

    assert result.tolist() == [
        [1.0, 1.0, 1.0, 1.0, 1.0],
        [1.0, 0.4, 0.4, 1.0, 1.0],
    ]


def test_manual_modulation_handles_multiple_and_overlapping_windows():
    factors = np.ones((2, 7))

    result = apply_manual_modulation(
        factors,
        (
            Modulation("P1", 1, 4, 0.5),
            Modulation("P1", 3, 6, 0.2),
            Modulation("P2", 0, 2, 0.8),
        ),
        ("P1", "P2"),
    )

    assert result.tolist() == [
        [1.0, 0.5, 0.5, 0.2, 0.2, 0.2, 1.0],
        [0.8, 0.8, 1.0, 1.0, 1.0, 1.0, 1.0],
    ]


@pytest.mark.parametrize(
    "modulation",
    [
        Modulation("UNKNOWN", 0, 1, 0.5),
        Modulation("P1", -1, 1, 0.5),
        Modulation("P1", 0, 5, 0.5),
        Modulation("P1", 2, 2, 0.5),
        Modulation("P1", 3, 2, 0.5),
        Modulation("P1", 0, 1, -0.1),
        Modulation("P1", 0, 1, 1.1),
        Modulation("P1", 0, 1, float("nan")),
    ],
)
def test_manual_modulation_rejects_invalid_input(modulation):
    with pytest.raises(ValueError):
        apply_manual_modulation(
            np.ones((1, 4)),
            (modulation,),
            ("P1",),
        )


def test_apply_maintenance_zeros_only_outage_days():
    factors = np.array([[0.9, 0.8, 0.7, 0.6]])
    mask = np.array([[False, True, False, True]])

    result = apply_maintenance(factors, mask)

    assert result.tolist() == [[0.9, 0.0, 0.7, 0.0]]


def test_maintenance_wins_when_applied_after_modulation():
    factors = np.ones((1, 4))
    mask = maintenance_mask(
        (Maintenance("P1", OutageKind.ASR, 1, 3),),
        ("P1",),
        4,
    )

    modulated = apply_manual_modulation(
        factors,
        (Modulation("P1", 1, 4, 0.5),),
        ("P1",),
    )
    result = apply_maintenance(modulated, mask)

    assert result.tolist() == [[1.0, 0.0, 0.0, 0.5]]


def test_apply_maintenance_rejects_shape_mismatch():
    with pytest.raises(ValueError):
        apply_maintenance(
            np.ones((1, 4)),
            np.zeros((2, 4), dtype=np.bool_),
        )


def test_functions_return_new_arrays_without_mutating_inputs():
    factors = np.ones((1, 4))
    factors_before = factors.copy()
    mask = np.zeros((1, 4), dtype=np.bool_)
    mask_before = mask.copy()

    modulated = apply_manual_modulation(
        factors,
        (Modulation("P1", 0, 2, 0.3),),
        ("P1",),
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
