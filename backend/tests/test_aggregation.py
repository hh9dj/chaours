import numpy as np

from chaours.aggregation import (
    daily_power_variation_mw,
    deficit_days,
    energy_mwh,
    national_supply,
)


def test_energy_mwh_multiplies_factor_power_and_hours():
    factors = np.array([[0.5, 1.0], [0.25, 0.75]], dtype=np.float64)

    result = energy_mwh(factors, np.array([1_000.0, 2_000.0]))

    assert result.dtype == np.float64
    np.testing.assert_allclose(
        result,
        [
            [12_000.0, 24_000.0],
            [12_000.0, 36_000.0],
        ],
    )


def test_national_supply_sums_plants_axis():
    energy = np.array([[10.0, 20.0, 30.0], [1.0, 2.0, 3.0]])

    result = national_supply(energy)

    assert result.shape == (3,)
    np.testing.assert_allclose(result, [11.0, 22.0, 33.0])


def test_deficit_days_returns_indices_below_demand():
    supply = np.array([100.0, 50.0, 99.0])
    demand = np.array([100.0, 60.0, 100.0])

    result = deficit_days(supply, demand)

    np.testing.assert_array_equal(result, [1, 2])


def test_deficit_days_is_strict_and_ignores_equality():
    supply = np.array([100.0, 100.0])
    demand = np.array([100.0, 100.0])

    result = deficit_days(supply, demand)

    assert result.size == 0
    assert result.dtype == np.intp


def test_daily_power_variation_returns_horizon_minus_one_values():
    energy = np.array([240.0, 480.0, 240.0])

    result = daily_power_variation_mw(energy)

    assert result.shape == (2,)
    np.testing.assert_allclose(result, [10.0, -10.0])


def test_daily_power_variation_supports_two_dimensions():
    energy = np.array(
        [
            [240.0, 480.0, 240.0],
            [0.0, 240.0, 720.0],
        ]
    )

    result = daily_power_variation_mw(energy)

    assert result.shape == (2, 2)
    np.testing.assert_allclose(result, [[10.0, -10.0], [10.0, 20.0]])
