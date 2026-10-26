from __future__ import annotations

from collections.abc import Generator

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlmodel import Session

from chaours.db.models import (
    MaintenanceTable,
    ModulationTable,
    PlantTable,
    ScenarioTable,
)
from chaours.db.repository import (
    create_scenario,
    delete_scenario,
    duplicate_scenario,
    get_scenario,
    replace_maintenances,
    replace_modulations,
)
from chaours.db.session import (
    build_engine,
    build_session_factory,
    create_db_and_tables,
)
from chaours.types import (
    Maintenance,
    Modulation,
    OutageKind,
    Plant,
    Scenario,
    Simulation,
)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = build_engine("sqlite://")
    create_db_and_tables(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as database_session:
        yield database_session


def _scenario(name: str = "scenario") -> Scenario:
    return Scenario(
        name=name,
        horizon_days=10,
        spot_prices=[10.5, 20.0, 30.25, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
        demand_mwh=[1_000.0] * 10,
        usage_values_eur_mwh={"P1": 60.5, "P2": 72.25},
        plants=[
            Simulation(
                plant=Plant(
                    id="P1",
                    eic_code="EIC-P1",
                    nominal_power_mw=900.0,
                    initial_jepp=300.5,
                ),
                maintenances=[Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3)],
                modulations=[Modulation(start_day=4, end_day=6, factor=0.5)],
            ),
            Simulation(
                plant=Plant(
                    id="P2",
                    eic_code="EIC-P2",
                    nominal_power_mw=1_300.25,
                    initial_jepp=280.0,
                ),
                maintenances=[Maintenance(kind=OutageKind.VD, start_day=7, end_day=9)],
            ),
        ],
    )


def _count(session: Session, model: type) -> int:
    count = session.scalar(select(func.count()).select_from(model))
    return int(count or 0)


def test_create_and_get_scenario_round_trip(session: Session):
    scenario = _scenario()

    created = create_scenario(session, scenario)
    loaded = get_scenario(session, scenario.scenario_id)

    assert loaded is not None
    assert created.scenario_id == scenario.scenario_id
    assert loaded.scenario_id == scenario.scenario_id
    assert loaded.name == "scenario"
    assert loaded.horizon_days == 10
    assert loaded.spot_prices == scenario.spot_prices
    assert loaded.demand_mwh == scenario.demand_mwh
    assert loaded.usage_values_eur_mwh == {
        "P1": 60.5,
        "P2": 72.25,
    }
    assert [entry.plant.id for entry in loaded.plants] == ["P1", "P2"]
    assert loaded.plants[0].plant.nominal_power_mw == 900.0
    assert loaded.plants[0].plant.initial_jepp == 300.5
    assert loaded.plants[0].maintenances == [
        Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3)
    ]
    assert loaded.plants[0].modulations == [Modulation(start_day=4, end_day=6, factor=0.5)]
    assert loaded.plants[1].maintenances == [
        Maintenance(kind=OutageKind.VD, start_day=7, end_day=9)
    ]


def test_get_unknown_scenario_returns_none(session: Session):
    assert get_scenario(session, _scenario().scenario_id) is None


def test_delete_scenario_cascades_to_plants_and_schedules(session: Session):
    scenario = _scenario()
    create_scenario(session, scenario)
    assert _count(session, PlantTable) == 2
    assert _count(session, MaintenanceTable) == 2
    assert _count(session, ModulationTable) == 1

    assert delete_scenario(session, scenario.scenario_id) is True
    assert get_scenario(session, scenario.scenario_id) is None
    assert _count(session, ScenarioTable) == 0
    assert _count(session, PlantTable) == 0
    assert _count(session, MaintenanceTable) == 0
    assert _count(session, ModulationTable) == 0


def test_delete_unknown_scenario_returns_false(session: Session):
    assert delete_scenario(session, _scenario().scenario_id) is False


def test_duplicate_scenario_gets_new_id_and_suffixed_name(session: Session):
    original = _scenario(name="plan")
    create_scenario(session, original)

    duplicate = duplicate_scenario(session, original.scenario_id)

    assert duplicate is not None
    assert duplicate.scenario_id != original.scenario_id
    assert duplicate.name == "plan (copie)"
    assert duplicate.usage_values_eur_mwh == original.usage_values_eur_mwh
    assert [entry.plant.id for entry in duplicate.plants] == ["P1", "P2"]
    assert duplicate.plants[0].maintenances == [
        Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3)
    ]
    assert get_scenario(session, duplicate.scenario_id) is not None
    assert get_scenario(session, original.scenario_id) is not None


def test_duplicate_name_is_trimmed_to_model_limit(session: Session):
    original = _scenario(name="x" * 200)
    create_scenario(session, original)

    duplicate = duplicate_scenario(session, original.scenario_id)

    assert duplicate is not None
    assert len(duplicate.name) == 200
    assert duplicate.name.endswith(" (copie)")


def test_duplicate_unknown_scenario_returns_none(session: Session):
    assert duplicate_scenario(session, _scenario().scenario_id) is None


def test_replace_maintenances_persists_validated_scenario(session: Session):
    scenario = _scenario()
    create_scenario(session, scenario)
    replacement = [Maintenance(kind=OutageKind.VP, start_day=2, end_day=4)]

    updated = replace_maintenances(
        session,
        scenario.scenario_id,
        "P1",
        replacement,
    )

    assert updated is not None
    assert updated.plants[0].maintenances == replacement
    loaded = get_scenario(session, scenario.scenario_id)
    assert loaded is not None
    assert loaded.plants[0].maintenances == replacement
    assert loaded.plants[1].maintenances == [
        Maintenance(kind=OutageKind.VD, start_day=7, end_day=9)
    ]


def test_replace_modulations_persists_validated_scenario(session: Session):
    scenario = _scenario()
    create_scenario(session, scenario)
    replacement = [Modulation(start_day=1, end_day=3, factor=0.25), Modulation(start_day=3, end_day=5, factor=0.75)]

    updated = replace_modulations(
        session,
        scenario.scenario_id,
        "P1",
        replacement,
    )

    assert updated is not None
    assert updated.plants[0].modulations == replacement
    loaded = get_scenario(session, scenario.scenario_id)
    assert loaded is not None
    assert loaded.plants[0].modulations == replacement


def test_replace_schedules_returns_none_for_unknown_scenario(session: Session):
    assert (
        replace_maintenances(
            session,
            _scenario().scenario_id,
            "P1",
            [],
        )
        is None
    )
    assert (
        replace_modulations(
            session,
            _scenario().scenario_id,
            "P1",
            [],
        )
        is None
    )


def test_replace_schedules_returns_none_for_unknown_plant(session: Session):
    scenario = _scenario()
    create_scenario(session, scenario)

    assert (
        replace_maintenances(
            session,
            scenario.scenario_id,
            "UNKNOWN",
            [],
        )
        is None
    )
    assert (
        replace_modulations(
            session,
            scenario.scenario_id,
            "UNKNOWN",
            [],
        )
        is None
    )


def test_replace_maintenances_rejects_overlap_without_persisting(
    session: Session,
):
    scenario = _scenario()
    create_scenario(session, scenario)

    with pytest.raises(ValidationError):
        replace_maintenances(
            session,
            scenario.scenario_id,
            "P1",
            [
                Maintenance(kind=OutageKind.ASR, start_day=1, end_day=4),
                Maintenance(kind=OutageKind.VP, start_day=3, end_day=5),
            ],
        )

    loaded = get_scenario(session, scenario.scenario_id)
    assert loaded is not None
    assert loaded.plants[0].maintenances == [
        Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3)
    ]


def test_replace_maintenances_rejects_window_outside_horizon(session: Session):
    scenario = _scenario()
    create_scenario(session, scenario)

    with pytest.raises(ValidationError):
        replace_maintenances(
            session,
            scenario.scenario_id,
            "P1",
            [Maintenance(kind=OutageKind.ASR, start_day=1, end_day=11)],
        )

    loaded = get_scenario(session, scenario.scenario_id)
    assert loaded is not None
    assert loaded.plants[0].maintenances == [
        Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3)
    ]


def test_scenarios_are_isolated(session: Session):
    first = _scenario(name="first")
    second = _scenario(name="second")
    create_scenario(session, first)
    create_scenario(session, second)

    replace_maintenances(
        session,
        first.scenario_id,
        "P1",
        [Maintenance(kind=OutageKind.VP, start_day=2, end_day=4)],
    )

    loaded_first = get_scenario(session, first.scenario_id)
    loaded_second = get_scenario(session, second.scenario_id)
    assert loaded_first is not None
    assert loaded_second is not None
    assert loaded_first.plants[0].maintenances == [
        Maintenance(kind=OutageKind.VP, start_day=2, end_day=4)
    ]
    assert loaded_second.plants[0].maintenances == [
        Maintenance(kind=OutageKind.ASR, start_day=1, end_day=3)
    ]
