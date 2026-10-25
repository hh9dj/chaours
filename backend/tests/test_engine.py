from dataclasses import replace
from typing import Any

import numpy as np
import pytest

from chaours.engine import NucliEngine
from chaours.types import (
    AlertKind,
    Maintenance,
    Modulation,
    OutageKind,
    Plant,
    Scenario,
    Simulation,
)


def _plant(
    plant_id: str = "P1",
    nominal_power_mw: float = 1_000.0,
    initial_jepp: float = 100.0,
) -> Plant:
    return Plant(
        id=plant_id,
        eic_code=f"EIC-{plant_id}",
        nominal_power_mw=nominal_power_mw,
        initial_jepp=initial_jepp,
    )


def _entry(
    plant: Plant | None = None,
    maintenances: tuple[Maintenance, ...] = (),
    modulations: tuple[Modulation, ...] = (),
) -> Simulation:
    return Simulation(
        plant if plant is not None else _plant(),
        list(maintenances),
        list(modulations),
    )


def _scenario(**overrides: Any) -> Scenario:
    horizon = 4
    base = Scenario(
        scenario_id="test",
        horizon_days=horizon,
        spot_prices=np.full(horizon, 80.0),
        demand_mwh=np.zeros(horizon),
        usage_values_eur_mwh={"P1": 60.0},
        plants=[_entry()],
    )
    return replace(base, **overrides)


def _maintenance(start_day: int, end_day: int) -> Maintenance:
    return Maintenance(OutageKind.ASR, start_day, end_day)


def test_engine_runs_full_pipeline_in_order():
    scenario = _scenario(
        horizon_days=5,
        spot_prices=np.full(5, 80.0),
        demand_mwh=np.zeros(5),
        plants=[
            _entry(
                _plant(initial_jepp=100.0),
                maintenances=(_maintenance(2, 3),),
                modulations=(Modulation(1, 4, 0.5),),
            )
        ],
    )

    result = NucliEngine().run(scenario)

    np.testing.assert_allclose(
        result.plants[0].production_factors,
        [1.0, 0.5, 0.0, 0.5, 1.0],
    )


def test_engine_returns_one_result_per_plant():
    scenario = _scenario(
        horizon_days=3,
        spot_prices=np.full(3, 80.0),
        demand_mwh=np.zeros(3),
        usage_values_eur_mwh={"P1": 60.0, "P2": 60.0},
        plants=[
            _entry(_plant("P1")),
            _entry(_plant("P2", 500.0)),
        ],
    )

    result = NucliEngine().run(scenario)

    assert [plant.plant_id for plant in result.plants] == ["P1", "P2"]


def test_engine_returns_national_supply_and_deficits():
    scenario = _scenario(
        horizon_days=3,
        spot_prices=np.full(3, 80.0),
        demand_mwh=np.array([5_000.0, 4_800.0, 4_000.0]),
        usage_values_eur_mwh={"P1": 60.0, "P2": 60.0},
        plants=[
            _entry(_plant("P1", 100.0)),
            _entry(_plant("P2", 100.0)),
        ],
    )

    result = NucliEngine().run(scenario)

    np.testing.assert_allclose(result.national_supply_mwh, [4_800.0] * 3)
    np.testing.assert_array_equal(result.deficit_days, [0])
    np.testing.assert_allclose(result.demand_mwh, [5_000.0, 4_800.0, 4_000.0])


def test_engine_recharge_resets_stock_and_restores_production():
    scenario = _scenario(
        horizon_days=6,
        spot_prices=np.full(6, 80.0),
        demand_mwh=np.zeros(6),
        plants=[
            _entry(
                _plant(initial_jepp=1.0),
                maintenances=(_maintenance(2, 3),),
            )
        ],
    )

    result = NucliEngine().run(scenario)

    plant_result = result.plants[0]
    np.testing.assert_allclose(
        plant_result.production_factors,
        [1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    )
    assert plant_result.production_factors[3] == 1.0
    assert plant_result.depletion_days == (1, 4)


def test_engine_depletion_clips_energy_and_supply():
    scenario = _scenario(
        horizon_days=2,
        spot_prices=np.full(2, 80.0),
        demand_mwh=np.zeros(2),
        plants=[
            _entry(_plant(nominal_power_mw=100.0, initial_jepp=0.5)),
        ],
    )

    result = NucliEngine().run(scenario)

    plant_result = result.plants[0]
    np.testing.assert_allclose(plant_result.production_factors, [0.5, 0.0])
    np.testing.assert_allclose(plant_result.energy_mwh, [1_200.0, 0.0])
    np.testing.assert_allclose(result.national_supply_mwh, [1_200.0, 0.0])
    assert plant_result.depletion_days == (0,)


def test_engine_alert_assembly_has_deterministic_order():
    scenario = _scenario(
        horizon_days=4,
        spot_prices=np.array([10.0, 100.0, 100.0, 100.0]),
        demand_mwh=np.array([0.0, 30_000.0, 0.0, 0.0]),
        plants=[_entry(_plant(initial_jepp=1.0))],
    )

    result = NucliEngine().run(scenario)

    assert [alert.kind for alert in result.alerts] == [
        AlertKind.NEUTRONIC_ANOMALY,
        AlertKind.REMIT_UMM,
        AlertKind.RTE_DEFICIT,
        AlertKind.SPOT_BELOW_USAGE_VALUE,
    ]
    assert result.alerts[0].day == 1
    assert result.alerts[1].day == 1
    assert result.alerts[2].day == 1
    assert result.alerts[3].day == 0


def test_engine_includes_spot_below_usage_value_alerts():
    scenario = _scenario(
        horizon_days=2,
        spot_prices=np.array([10.0, 50.0]),
        demand_mwh=np.zeros(2),
        plants=[_entry(_plant(initial_jepp=100.0))],
    )

    result = NucliEngine().run(scenario)

    assert [alert.kind for alert in result.alerts] == [
        AlertKind.SPOT_BELOW_USAGE_VALUE,
        AlertKind.SPOT_BELOW_USAGE_VALUE,
    ]


def _invalid_scenarios() -> list[Scenario]:
    return [
        _scenario(
            horizon_days=0,
            spot_prices=np.array([]),
            demand_mwh=np.array([]),
        ),
        _scenario(spot_prices=np.ones((1, 4))),
        _scenario(spot_prices=np.ones(3)),
        _scenario(demand_mwh=np.ones((1, 4))),
        _scenario(demand_mwh=np.ones(3)),
        _scenario(plants=[], usage_values_eur_mwh={}),
        _scenario(
            plants=[
                _entry(_plant("P1")),
                _entry(_plant("P1")),
            ]
        ),
        _scenario(
            plants=[_entry(_plant(nominal_power_mw=-1.0))],
        ),
        _scenario(
            plants=[_entry(_plant(initial_jepp=-1.0))],
        ),
        _scenario(usage_values_eur_mwh={"P2": 60.0}),
        _scenario(
            plants=[
                _entry(
                    maintenances=(
                        _maintenance(1, 3),
                        _maintenance(2, 4),
                    )
                )
            ]
        ),
        _scenario(
            plants=[
                _entry(maintenances=(_maintenance(3, 2),)),
            ]
        ),
        _scenario(
            plants=[
                _entry(modulations=(Modulation(2, 2, 0.5),)),
            ]
        ),
        _scenario(
            plants=[
                _entry(modulations=(Modulation(0, 1, 1.5),)),
            ]
        ),
    ]


@pytest.mark.parametrize("scenario", _invalid_scenarios())
def test_engine_rejects_invalid_scenarios(scenario: Scenario):
    with pytest.raises(ValueError):
        NucliEngine().run(scenario)


def test_engine_execution_time_is_non_negative():
    result = NucliEngine().run(_scenario())

    assert result.execution_time_ms >= 0.0
