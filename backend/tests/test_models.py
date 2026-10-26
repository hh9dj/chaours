from __future__ import annotations

import math
from datetime import timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from chaours.types import (
    Alert,
    AlertKind,
    Maintenance,
    Modulation,
    OutageKind,
    Plant,
    PlantResult,
    Scenario,
    Severity,
    Simulation,
    SimulationResult,
)


def _plant(plant_id: str = "P1") -> Plant:
    return Plant(
        id=plant_id,
        eic_code=f"EIC-{plant_id}",
        nominal_power_mw=900.0,
        initial_jepp=300.0,
    )


def _entry(
    plant_id: str = "P1",
    maintenances: list[Maintenance] | None = None,
    modulations: list[Modulation] | None = None,
) -> Simulation:
    return Simulation(
        plant=_plant(plant_id),
        maintenances=list(maintenances or []),
        modulations=list(modulations or []),
    )


def _scenario(**overrides: Any) -> Scenario:
    data: dict[str, Any] = {
        "name": "scenario",
        "horizon_days": 4,
        "spot_prices": [80.0, 80.0, 80.0, 80.0],
        "demand_mwh": [0.0, 0.0, 0.0, 0.0],
        "usage_values_eur_mwh": {"P1": 60.0},
        "plants": [_entry()],
    }
    data.update(overrides)
    return Scenario(**data)


def _plant_result(**overrides: Any) -> PlantResult:
    data: dict[str, Any] = {
        "plant_id": "P1",
        "production_factors": [1.0, 0.5],
        "energy_mwh": [100.0, 50.0],
        "remaining_jepp": [10.0, 5.0],
        "depletion_days": [],
    }
    data.update(overrides)
    return PlantResult(**data)


def _simulation_result(**overrides: Any) -> SimulationResult:
    data: dict[str, Any] = {
        "scenario_id": uuid4(),
        "execution_time_ms": 1.0,
        "plants": [_plant_result()],
        "national_supply_mwh": [100.0, 50.0],
        "demand_mwh": [0.0, 0.0],
        "deficit_days": [],
        "alerts": [],
    }
    data.update(overrides)
    return SimulationResult(**data)


def test_scenario_defaults_generate_uuid_and_utc_timestamp():
    scenario = _scenario()

    assert isinstance(scenario.scenario_id, UUID)
    assert scenario.created_at.tzinfo == timezone.utc


def test_plant_rejects_empty_ids_and_invalid_values():
    with pytest.raises(ValidationError):
        Plant(
            id="",
            eic_code="EIC",
            nominal_power_mw=900.0,
            initial_jepp=300.0,
        )
    with pytest.raises(ValidationError):
        Plant(
            id="P1",
            eic_code="",
            nominal_power_mw=900.0,
            initial_jepp=300.0,
        )
    with pytest.raises(ValidationError):
        Plant(
            id="P1",
            eic_code="EIC",
            nominal_power_mw=0.0,
            initial_jepp=300.0,
        )
    with pytest.raises(ValidationError):
        Plant(
            id="P1",
            eic_code="EIC",
            nominal_power_mw=900.0,
            initial_jepp=-1.0,
        )


@pytest.mark.parametrize(
    "maintenance",
    [
        {"kind": "ASR", "start_day": -1, "end_day": 2},
        {"kind": "ASR", "start_day": 2, "end_day": 2},
        {"kind": "ASR", "start_day": 3, "end_day": 2},
    ],
)
def test_maintenance_rejects_invalid_windows(maintenance: dict[str, Any]):
    with pytest.raises(ValidationError):
        Maintenance(**maintenance)


@pytest.mark.parametrize(
    "modulation",
    [
        {"start_day": -1, "end_day": 2, "factor": 0.5},
        {"start_day": 2, "end_day": 2, "factor": 0.5},
        {"start_day": 3, "end_day": 2, "factor": 0.5},
        {"start_day": 0, "end_day": 2, "factor": -0.1},
        {"start_day": 0, "end_day": 2, "factor": 1.1},
        {"start_day": 0, "end_day": 2, "factor": math.nan},
    ],
)
def test_modulation_rejects_invalid_windows_and_factors(
    modulation: dict[str, Any],
):
    with pytest.raises(ValidationError):
        Modulation(**modulation)


def test_models_reject_extra_fields():
    with pytest.raises(ValidationError):
        Plant.model_validate(
            {
                "id": "P1",
                "eic_code": "EIC",
                "nominal_power_mw": 900.0,
                "initial_jepp": 300.0,
                "extra": 1,
            }
        )


def test_simulation_rejects_overlapping_maintenances():
    with pytest.raises(ValidationError):
        _entry(
            maintenances=[
                Maintenance(kind=OutageKind.ASR, start_day=1, end_day=4),
                Maintenance(kind=OutageKind.VP, start_day=3, end_day=5),
            ]
        )


def test_simulation_allows_touching_maintenances():
    entry = _entry(
        maintenances=[
            Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3),
            Maintenance(kind=OutageKind.VP, start_day=3, end_day=5),
        ]
    )

    assert len(entry.maintenances) == 2


def test_simulation_rejects_overlapping_modulations():
    with pytest.raises(ValidationError):
        _entry(
            modulations=[
                Modulation(start_day=1, end_day=4, factor=0.5),
                Modulation(start_day=3, end_day=5, factor=0.6),
            ]
        )


def test_simulation_allows_touching_modulations():
    entry = _entry(
        modulations=[
            Modulation(start_day=1, end_day=3, factor=0.5),
            Modulation(start_day=3, end_day=5, factor=0.6),
        ]
    )

    assert len(entry.modulations) == 2


@pytest.mark.parametrize("horizon_days", [0, -1, 7306])
def test_scenario_rejects_invalid_horizon(horizon_days: int):
    with pytest.raises(ValidationError):
        _scenario(horizon_days=horizon_days)


def test_scenario_accepts_maximum_horizon():
    horizon = 7305
    scenario = _scenario(
        horizon_days=horizon,
        spot_prices=[80.0] * horizon,
        demand_mwh=[0.0] * horizon,
    )

    assert scenario.horizon_days == horizon


def test_scenario_requires_at_least_one_plant():
    with pytest.raises(ValidationError):
        _scenario(plants=[], usage_values_eur_mwh={})


def test_scenario_requires_unique_plant_ids():
    with pytest.raises(ValidationError):
        _scenario(
            plants=[_entry("P1"), _entry("P1")],
            usage_values_eur_mwh={"P1": 60.0},
        )


def test_scenario_requires_exact_usage_value_mapping():
    with pytest.raises(ValidationError):
        _scenario(usage_values_eur_mwh={})
    with pytest.raises(ValidationError):
        _scenario(usage_values_eur_mwh={"P1": 60.0, "P2": 70.0})


def test_scenario_requires_array_lengths_to_match_horizon():
    with pytest.raises(ValidationError):
        _scenario(spot_prices=[80.0] * 3)
    with pytest.raises(ValidationError):
        _scenario(demand_mwh=[0.0] * 3)


@pytest.mark.parametrize(
    "overrides",
    [
        {"spot_prices": [80.0, math.inf, 80.0, 80.0]},
        {"spot_prices": [80.0, math.nan, 80.0, 80.0]},
        {"demand_mwh": [0.0, math.inf, 0.0, 0.0]},
        {"demand_mwh": [0.0, math.nan, 0.0, 0.0]},
        {"usage_values_eur_mwh": {"P1": math.inf}},
        {"usage_values_eur_mwh": {"P1": math.nan}},
    ],
)
def test_scenario_rejects_non_finite_values(overrides: dict[str, Any]):
    with pytest.raises(ValidationError):
        _scenario(**overrides)


def test_scenario_rejects_negative_demand():
    with pytest.raises(ValidationError):
        _scenario(demand_mwh=[0.0, -1.0, 0.0, 0.0])


def test_scenario_rejects_windows_outside_the_horizon():
    with pytest.raises(ValidationError):
        _scenario(
            plants=[
                _entry(
                    maintenances=[Maintenance(kind=OutageKind.ASR, start_day=1, end_day=5)],
                )
            ]
        )
    with pytest.raises(ValidationError):
        _scenario(
            plants=[_entry(modulations=[Modulation(start_day=1, end_day=5, factor=0.5)])]
        )


def test_scenario_validation_runs_on_assignment():
    scenario = _scenario()

    with pytest.raises(ValidationError):
        scenario.horizon_days = 0


def test_plant_result_rejects_invalid_production_factors():
    with pytest.raises(ValidationError):
        _plant_result(production_factors=[1.0, 1.5])
    with pytest.raises(ValidationError):
        _plant_result(production_factors=[-0.1, 0.5])
    with pytest.raises(ValidationError):
        _plant_result(production_factors=[math.nan, 0.5])
    with pytest.raises(ValidationError):
        _plant_result(production_factors=[math.inf, 0.5])


def test_plant_result_rejects_negative_or_non_finite_arrays():
    with pytest.raises(ValidationError):
        _plant_result(energy_mwh=[100.0, -1.0])
    with pytest.raises(ValidationError):
        _plant_result(remaining_jepp=[10.0, -1.0])
    with pytest.raises(ValidationError):
        _plant_result(energy_mwh=[100.0, math.inf])
    with pytest.raises(ValidationError):
        _plant_result(remaining_jepp=[10.0, math.nan])


def test_plant_result_requires_ascending_depletion_days():
    with pytest.raises(ValidationError):
        _plant_result(depletion_days=[3, 1])


def test_plant_result_requires_equal_array_lengths():
    with pytest.raises(ValidationError):
        _plant_result(energy_mwh=[100.0])


def test_simulation_result_requires_matching_supply_and_demand():
    with pytest.raises(ValidationError):
        _simulation_result(national_supply_mwh=[100.0])


def test_simulation_result_requires_plant_arrays_to_match_horizon():
    with pytest.raises(ValidationError):
        _simulation_result(
            plants=[
                _plant_result(
                    production_factors=[1.0],
                    energy_mwh=[100.0],
                    remaining_jepp=[10.0],
                )
            ]
        )


def test_simulation_result_rejects_days_outside_horizon():
    with pytest.raises(ValidationError):
        _simulation_result(deficit_days=[2])
    with pytest.raises(ValidationError):
        _simulation_result(
            plants=[_plant_result(depletion_days=[2])]
        )
    with pytest.raises(ValidationError):
        _simulation_result(
            alerts=[
                Alert(
                    kind=AlertKind.REMIT_UMM,
                    day=2,
                    plant_id="P1",
                    message="Alerte.",
                    severity=Severity.WARNING,
                )
            ]
        )


def test_simulation_result_requires_unique_plant_ids():
    with pytest.raises(ValidationError):
        _simulation_result(plants=[_plant_result(), _plant_result()])


def test_simulation_result_rejects_negative_execution_time():
    with pytest.raises(ValidationError):
        _simulation_result(execution_time_ms=-1.0)


def test_simulation_result_accepts_alerts_without_day():
    result = _simulation_result(
        alerts=[
            Alert(
                kind=AlertKind.NEUTRONIC_ANOMALY,
                day=None,
                plant_id="P1",
                message="Alerte.",
                severity=Severity.CRITICAL,
            )
        ]
    )

    assert result.alerts[0].day is None
