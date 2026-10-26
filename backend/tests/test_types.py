from __future__ import annotations

from uuid import uuid4

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


def _scenario() -> Scenario:
    return Scenario(
        name="test",
        horizon_days=4,
        spot_prices=[80.0] * 4,
        demand_mwh=[0.0] * 4,
        usage_values_eur_mwh={"P1": 60.0, "P2": 60.0},
        plants=[_entry("P1"), _entry("P2")],
    )


def test_simulation_starts_with_empty_schedule_lists():
    entry = Simulation(plant=_plant())

    assert entry.maintenances == []
    assert entry.modulations == []


def test_schedules_are_owned_by_the_simulation_entry():
    entry = _entry(
        maintenances=[Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3)],
        modulations=[Modulation(start_day=2, end_day=4, factor=0.5)],
    )

    assert entry.maintenances[0].kind == OutageKind.ASR
    assert entry.maintenances[0].start_day == 1
    assert entry.maintenances[0].end_day == 3
    assert entry.modulations[0].factor == 0.5


def test_scenario_schedule_mappings_keep_entry_order():
    scenario = _scenario()
    scenario.plants[0].maintenances = [Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3)]
    scenario.plants[1].maintenances = [Maintenance(kind=OutageKind.VP, start_day=2, end_day=4)]
    scenario.plants[0].modulations = [Modulation(start_day=1, end_day=2, factor=0.5)]
    scenario.plants[1].modulations = [Modulation(start_day=2, end_day=3, factor=0.7)]

    assert list(scenario.maintenances_by_plant) == ["P1", "P2"]
    assert list(scenario.modulations_by_plant) == ["P1", "P2"]
    assert scenario.maintenances_by_plant["P2"] == (
        Maintenance(kind=OutageKind.VP, start_day=2, end_day=4),
    )
    assert scenario.modulations_by_plant["P1"] == (Modulation(start_day=1, end_day=2, factor=0.5),)


def test_result_alerts_are_grouped_by_plant_and_national():
    plant_alert = Alert(
        kind=AlertKind.REMIT_UMM,
        day=1,
        plant_id="P1",
        message="Alerte tranche.",
        severity=Severity.WARNING,
    )
    national_alert = Alert(
        kind=AlertKind.RTE_DEFICIT,
        day=2,
        plant_id=None,
        message="Alerte nationale.",
        severity=Severity.CRITICAL,
    )
    result = SimulationResult(
        scenario_id=uuid4(),
        execution_time_ms=1.0,
        plants=[
            PlantResult(
                plant_id="P1",
                production_factors=[1.0, 1.0, 1.0],
                energy_mwh=[1.0, 1.0, 1.0],
                remaining_jepp=[1.0, 1.0, 1.0],
                depletion_days=[],
            )
        ],
        national_supply_mwh=[1.0, 1.0, 1.0],
        demand_mwh=[0.0, 0.0, 0.0],
        deficit_days=[2],
        alerts=[plant_alert, national_alert],
    )

    assert result.alerts_by_plant == {"P1": (plant_alert,)}
    assert result.national_alerts == (national_alert,)
