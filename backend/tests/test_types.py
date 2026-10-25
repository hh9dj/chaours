from dataclasses import fields

import numpy as np

from chaours.types import (
    Maintenance,
    Modulation,
    OutageKind,
    Plant,
    Scenario,
    Simulation,
)


def _plant(plant_id: str = "P1") -> Plant:
    return Plant(
        id=plant_id,
        eic_code=f"EIC-{plant_id}",
        nominal_power_mw=900.0,
        initial_jepp=300.0,
    )


def _scenario(scenario_id: str = "test") -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        horizon_days=4,
        spot_prices=np.full(4, 80.0),
        demand_mwh=np.zeros(4),
        usage_values_eur_mwh={"P1": 60.0},
    )


def test_scenario_plant_starts_with_empty_schedule_lists():
    entry = Simulation(_plant())

    assert entry.maintenances == []
    assert entry.modulations == []


def test_schedule_records_do_not_carry_plant_ids():
    maintenance_fields = {field.name for field in fields(Maintenance)}
    modulation_fields = {field.name for field in fields(Modulation)}

    assert "plant_id" not in maintenance_fields
    assert "plant_id" not in modulation_fields


def test_scenario_plant_add_helpers_populate_owner_lists():
    entry = Simulation(_plant())

    maintenance = entry.add_maintenance(OutageKind.ASR, 1, 3)
    modulation = entry.add_modulation(2, 4, 0.5)

    assert entry.maintenances == [maintenance]
    assert entry.modulations == [modulation]
    assert maintenance.kind == OutageKind.ASR
    assert maintenance.start_day == 1
    assert maintenance.end_day == 3
    assert modulation.factor == 0.5


def test_scenario_add_plant_returns_the_new_entry():
    scenario = _scenario()

    entry = scenario.add_plant(_plant("P1"))

    assert scenario.plants == [entry]
    assert entry.plant.id == "P1"


def test_shared_plant_configuration_does_not_share_schedule_lists():
    plant = _plant("P1")
    first_scenario = _scenario("first")
    second_scenario = _scenario("second")

    first = first_scenario.add_plant(plant)
    second = second_scenario.add_plant(plant)
    first.add_maintenance(OutageKind.ASR, 1, 3)
    first.add_modulation(1, 2, 0.5)

    assert second.maintenances == []
    assert second.modulations == []
    assert first_scenario.maintenances_by_plant["P1"] == (
        Maintenance(OutageKind.ASR, 1, 3),
    )
    assert second_scenario.maintenances_by_plant["P1"] == ()


def test_scenario_schedule_mappings_keep_entry_order():
    scenario = _scenario()
    first = scenario.add_plant(_plant("P1"))
    second = scenario.add_plant(_plant("P2"))
    first.add_maintenance(OutageKind.ASR, 1, 3)
    second.add_maintenance(OutageKind.VP, 2, 4)
    first.add_modulation(1, 2, 0.5)
    second.add_modulation(2, 3, 0.7)

    assert list(scenario.maintenances_by_plant) == ["P1", "P2"]
    assert list(scenario.modulations_by_plant) == ["P1", "P2"]
    assert scenario.maintenances_by_plant["P2"] == (Maintenance(OutageKind.VP, 2, 4),)
    assert scenario.modulations_by_plant["P1"] == (Modulation(1, 2, 0.5),)
