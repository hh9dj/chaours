import numpy as np

from chaours.jepp import simulate_stock_cycles
from chaours.types import FloatArray, Maintenance, OutageKind


def _factors(*values: float) -> FloatArray:
    return np.array(values, dtype=np.float64)


def _maintenance(start_day: int, end_day: int) -> Maintenance:
    return Maintenance(
        kind=OutageKind.ASR,
        start_day=start_day,
        end_day=end_day,
    )


def test_no_depletion_when_stock_is_sufficient():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.5, 0.5, 0.5), 2.0, ()
    )

    np.testing.assert_allclose(actual, [0.5, 0.5, 0.5])
    np.testing.assert_allclose(remaining, [1.5, 1.0, 0.5])
    assert depletion == ()


def test_exact_consumption_at_stop_start_is_not_a_deficit():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.5, 0.5, 0.5, 0.0), 1.5, (_maintenance(3, 4),)
    )

    np.testing.assert_allclose(actual, [0.5, 0.5, 0.5, 0.0])
    np.testing.assert_allclose(remaining, [1.0, 0.5, 0.0, 0.0])
    assert depletion == ()


def test_first_deficit_clips_production_to_remaining_stock():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.4, 0.4, 0.4, 0.4), 1.0, ()
    )

    np.testing.assert_allclose(actual, [0.4, 0.4, 0.2, 0.0])
    np.testing.assert_allclose(remaining, [0.6, 0.2, 0.0, 0.0])
    assert depletion == (2,)


def test_production_stays_zero_after_deficit_until_recharge():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.6, 0.6, 0.6, 0.0, 0.6), 1.0, (_maintenance(3, 4),)
    )

    np.testing.assert_allclose(actual, [0.6, 0.4, 0.0, 0.0, 0.6])
    np.testing.assert_allclose(remaining, [0.4, 0.0, 0.0, 0.0, 0.4])
    assert depletion == (1,)


def test_recharge_resets_stock_at_stop_end():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.5, 0.5, 0.0, 0.5, 0.5), 1.0, (_maintenance(2, 3),)
    )

    np.testing.assert_allclose(actual, [0.5, 0.5, 0.0, 0.5, 0.5])
    np.testing.assert_allclose(remaining, [0.5, 0.0, 0.0, 0.5, 0.0])
    assert depletion == ()


def test_zero_outage_days_keep_stock_constant_until_stop_end():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.75, 0.0, 0.0, 0.25), 1.0, (_maintenance(1, 3),)
    )

    np.testing.assert_allclose(actual, [0.75, 0.0, 0.0, 0.25])
    np.testing.assert_allclose(remaining, [0.25, 0.25, 0.25, 0.75])
    assert depletion == ()


def test_multiple_stops_create_independent_cycles():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.25, 0.25, 0.0, 0.25, 0.25, 0.0, 0.25, 0.25),
        1.0,
        (_maintenance(2, 3), _maintenance(5, 6)),
    )

    np.testing.assert_allclose(actual, [0.25, 0.25, 0.0, 0.25, 0.25, 0.0, 0.25, 0.25])
    np.testing.assert_allclose(remaining, [0.75, 0.5, 0.5, 0.75, 0.5, 0.5, 0.75, 0.5])
    assert depletion == ()


def test_multiple_cycles_can_each_produce_a_depletion_day():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.6, 0.6, 0.0, 0.6, 0.6, 0.6, 0.0, 0.6, 0.6),
        1.0,
        (_maintenance(2, 3), _maintenance(6, 7)),
    )

    np.testing.assert_allclose(actual, [0.6, 0.4, 0.0, 0.6, 0.4, 0.0, 0.0, 0.6, 0.4])
    np.testing.assert_allclose(remaining, [0.4, 0.0, 0.0, 0.4, 0.0, 0.0, 0.0, 0.4, 0.0])
    assert depletion == (1, 4, 8)


def test_depletion_in_final_cycle_is_recorded_without_future_stop():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.5, 0.5, 0.6), 1.0, ()
    )

    np.testing.assert_allclose(actual, [0.5, 0.5, 0.0])
    np.testing.assert_allclose(remaining, [0.5, 0.0, 0.0])
    assert depletion == (2,)


def test_empty_maintenance_list_produces_a_single_cycle():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.5, 0.6), 1.0, ()
    )

    np.testing.assert_allclose(actual, [0.5, 0.5])
    np.testing.assert_allclose(remaining, [0.5, 0.0])
    assert depletion == (1,)


def test_zero_initial_stock_with_positive_request_is_deficit_on_day_zero():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.5, 0.5), 0.0, ()
    )

    np.testing.assert_allclose(actual, [0.0, 0.0])
    np.testing.assert_allclose(remaining, [0.0, 0.0])
    assert depletion == (0,)


def test_unsorted_maintenances_are_handled_chronologically():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.25, 0.25, 0.0, 0.25, 0.0, 0.25),
        1.0,
        (_maintenance(4, 5), _maintenance(2, 3)),
    )

    np.testing.assert_allclose(actual, [0.25, 0.25, 0.0, 0.25, 0.0, 0.25])
    np.testing.assert_allclose(remaining, [0.75, 0.5, 0.5, 0.75, 0.75, 0.75])
    assert depletion == ()


def test_remaining_jepp_is_clamped_at_zero():
    actual, remaining, depletion = simulate_stock_cycles(
        _factors(0.8, 0.8), 0.5, ()
    )

    np.testing.assert_allclose(actual, [0.5, 0.0])
    np.testing.assert_allclose(remaining, [0.0, 0.0])
    assert np.all(remaining >= 0.0)
    assert depletion == (0,)


def test_inputs_are_not_mutated():
    requested = _factors(0.5, 0.0, 0.0, 0.5)
    requested_before = requested.copy()
    maintenances = [_maintenance(1, 3)]
    maintenances_before = list(maintenances)

    simulate_stock_cycles(requested, 2.0, maintenances)

    np.testing.assert_array_equal(requested, requested_before)
    assert maintenances == maintenances_before


def test_empty_horizon_returns_empty_outputs():
    actual, remaining, depletion = simulate_stock_cycles(_factors(), 0.0, ())

    assert actual.shape == (0,)
    assert remaining.shape == (0,)
    assert depletion == ()
