from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel import Session

from chaours.db.models import (
    MaintenanceTable,
    ModulationTable,
    PlantTable,
    ScenarioTable,
)
from chaours.types import (
    Maintenance,
    Modulation,
    Plant,
    Simulation,
    Scenario,
)


def _plant_to_table(
    entry: Simulation,
    scenario_id: UUID,
) -> PlantTable:
    return PlantTable(
        scenario_id=scenario_id,
        plant_id=entry.plant.id,
        eic_code=entry.plant.eic_code,
        nominal_power_mw=entry.plant.nominal_power_mw,
        initial_jepp=entry.plant.initial_jepp,
        maintenances=[
            MaintenanceTable(  # type: ignore[call-arg]
                kind=maintenance.kind,
                start_day=maintenance.start_day,
                end_day=maintenance.end_day,
            )
            for maintenance in entry.maintenances
        ],
        modulations=[
            ModulationTable(  # type: ignore[call-arg]
                start_day=modulation.start_day,
                end_day=modulation.end_day,
                factor=modulation.factor,
            )
            for modulation in entry.modulations
        ],
    )


def _scenario_to_table(scenario: Scenario) -> ScenarioTable:
    return ScenarioTable(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        created_at=scenario.created_at,
        horizon_days=scenario.horizon_days,
        spot_prices=list(scenario.spot_prices),
        demand_mwh=list(scenario.demand_mwh),
        usage_values_eur_mwh=dict(scenario.usage_values_eur_mwh),
        plants=[
            _plant_to_table(entry, scenario.scenario_id) for entry in scenario.plants
        ],
    )


def _plant_from_table(plant: PlantTable) -> Simulation:
    maintenances = sorted(
        plant.maintenances,
        key=lambda maintenance: maintenance.id or 0,
    )
    modulations = sorted(
        plant.modulations,
        key=lambda modulation: modulation.id or 0,
    )
    return Simulation(
        plant=Plant(
            id=plant.plant_id,
            eic_code=plant.eic_code,
            nominal_power_mw=plant.nominal_power_mw,
            initial_jepp=plant.initial_jepp,
        ),
        maintenances=[
            Maintenance(
                kind=maintenance.kind,
                start_day=maintenance.start_day,
                end_day=maintenance.end_day,
            )
            for maintenance in maintenances
        ],
        modulations=[
            Modulation(
                start_day=modulation.start_day,
                end_day=modulation.end_day,
                factor=modulation.factor,
            )
            for modulation in modulations
        ],
    )


def _scenario_from_table(row: ScenarioTable) -> Scenario:
    plants = sorted(row.plants, key=lambda plant: plant.id or 0)
    return Scenario(
        scenario_id=row.scenario_id,
        name=row.name,
        created_at=row.created_at,
        horizon_days=row.horizon_days,
        spot_prices=list(row.spot_prices),
        demand_mwh=list(row.demand_mwh),
        usage_values_eur_mwh=dict(row.usage_values_eur_mwh),
        plants=[_plant_from_table(plant) for plant in plants],
    )


def _replace_scenario(session: Session, scenario: Scenario) -> Scenario:
    existing = session.get(ScenarioTable, scenario.scenario_id)
    if existing is not None:
        session.delete(existing)
        session.flush()

    row = _scenario_to_table(scenario)
    session.add(row)
    session.commit()
    return _scenario_from_table(row)


def create_scenario(session: Session, scenario: Scenario) -> Scenario:
    """Persiste un scénario complet et le renvoie."""
    row = _scenario_to_table(scenario)
    session.add(row)
    session.commit()
    return _scenario_from_table(row)


def get_scenario(
    session: Session,
    scenario_id: UUID,
) -> Scenario | None:
    """Charge et reconstruit un scénario complet, ou ``None``."""
    row = session.get(ScenarioTable, scenario_id)
    if row is None:
        return None
    return _scenario_from_table(row)


def delete_scenario(session: Session, scenario_id: UUID) -> bool:
    """Supprime un scénario et ses dépendances."""
    row = session.get(ScenarioTable, scenario_id)
    if row is None:
        return False
    session.delete(row)
    session.commit()
    return True


def _duplicate_name(name: str) -> str:
    suffix = " (copie)"
    return f"{name[: 200 - len(suffix)]}{suffix}"


def duplicate_scenario(
    session: Session,
    scenario_id: UUID,
) -> Scenario | None:
    """Duplique un scénario avec un nouvel identifiant et un nom suffixé."""
    original = get_scenario(session, scenario_id)
    if original is None:
        return None

    duplicate = Scenario(
        scenario_id=uuid4(),
        name=_duplicate_name(original.name),
        created_at=datetime.now(UTC),
        horizon_days=original.horizon_days,
        spot_prices=list(original.spot_prices),
        demand_mwh=list(original.demand_mwh),
        usage_values_eur_mwh=dict(original.usage_values_eur_mwh),
        plants=[
            Simulation(
                plant=entry.plant,
                maintenances=list(entry.maintenances),
                modulations=list(entry.modulations),
            )
            for entry in original.plants
        ],
    )
    return create_scenario(session, duplicate)


def _with_replaced_schedule(
    scenario: Scenario,
    plant_id: str,
    maintenances: list[Maintenance] | None,
    modulations: list[Modulation] | None,
) -> Scenario | None:
    if plant_id not in {entry.plant.id for entry in scenario.plants}:
        return None

    plants = [
        Simulation(
            plant=entry.plant,
            maintenances=(
                list(maintenances)
                if maintenances is not None and entry.plant.id == plant_id
                else list(entry.maintenances)
            ),
            modulations=(
                list(modulations)
                if modulations is not None and entry.plant.id == plant_id
                else list(entry.modulations)
            ),
        )
        for entry in scenario.plants
    ]

    return Scenario(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        created_at=scenario.created_at,
        horizon_days=scenario.horizon_days,
        spot_prices=list(scenario.spot_prices),
        demand_mwh=list(scenario.demand_mwh),
        usage_values_eur_mwh=dict(scenario.usage_values_eur_mwh),
        plants=plants,
    )


def replace_maintenances(
    session: Session,
    scenario_id: UUID,
    plant_id: str,
    maintenances: list[Maintenance],
) -> Scenario | None:
    """Remplace les arrêts d'une tranche, puis persiste le scénario validé."""
    scenario = get_scenario(session, scenario_id)
    if scenario is None:
        return None
    updated = _with_replaced_schedule(
        scenario,
        plant_id,
        maintenances,
        None,
    )
    if updated is None:
        return None
    return _replace_scenario(session, updated)


def replace_modulations(
    session: Session,
    scenario_id: UUID,
    plant_id: str,
    modulations: list[Modulation],
) -> Scenario | None:
    """Remplace les modulations d'une tranche, puis persiste le scénario."""
    scenario = get_scenario(session, scenario_id)
    if scenario is None:
        return None
    updated = _with_replaced_schedule(
        scenario,
        plant_id,
        None,
        modulations,
    )
    if updated is None:
        return None
    return _replace_scenario(session, updated)
