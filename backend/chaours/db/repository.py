from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlmodel import Session, select

from chaours.db.models import (
    ArretTable,
    DonneeJournaliereTable,
    ModulationTable,
    SimulationTable,
    TrancheTable,
)
from chaours.types import (
    Arret,
    ConfigurationTranche,
    Modulation,
    ParametresSimulation,
    Simulation,
    SimulationCreation,
    SimulationResume,
    SimulationTranche,
    Tranche,
)


def _persist(session: Session, simulation: Simulation) -> Simulation:
    session.add(
        SimulationTable(
            simulation_id=simulation.simulation_id,
            nom=simulation.nom,
            cree_le=simulation.cree_le,
            horizon_jours=simulation.horizon_jours,
        )
    )
    session.flush()

    for jour in range(simulation.horizon_jours):
        session.add(
            DonneeJournaliereTable(
                simulation_id=simulation.simulation_id,
                jour=jour,
                prix_spot_eur_mwh=simulation.prix_spot_eur_mwh[jour],
                demande_nationale_mwh=simulation.demande_nationale_mwh[jour],
                valeur_usage_eur_mwh=simulation.valeur_usage_eur_mwh[jour],
            )
        )

    for entry in simulation.tranches:
        tranche_id = entry.tranche.identifiant
        session.add(
            TrancheTable(
                simulation_id=simulation.simulation_id,
                identifiant=tranche_id,
                code_eic=entry.tranche.code_eic,
                jepp_initial=entry.tranche.jepp_initial,
                puissance_nominale_mw=entry.tranche.puissance_nominale_mw,
            )
        )
        session.flush()
        for arret in entry.arrets:
            session.add(
                ArretTable(
                    simulation_id=simulation.simulation_id,
                    tranche_id=tranche_id,
                    type_arret=arret.type_arret,
                    jour_debut=arret.jour_debut,
                    jour_fin=arret.jour_fin,
                )
            )
        for modulation in entry.modulations:
            session.add(
                ModulationTable(
                    simulation_id=simulation.simulation_id,
                    tranche_id=tranche_id,
                    jour_debut=modulation.jour_debut,
                    jour_fin=modulation.jour_fin,
                    facteur=modulation.facteur,
                )
            )

    session.commit()
    return simulation


def _replace(session: Session, simulation: Simulation) -> Simulation:
    existing = session.get(SimulationTable, simulation.simulation_id)
    if existing is not None:
        session.delete(existing)
        session.flush()
    session.expunge_all()
    return _persist(session, simulation)


def _check_daily_rows(
    rows: list[DonneeJournaliereTable],
    horizon_jours: int,
    simulation_id: UUID,
) -> None:
    jours = [row.jour for row in rows]
    expected = list(range(horizon_jours))
    if jours != expected:
        raise ValueError(
            "donnees_journalieres rows must be exactly 0.."
            f"{horizon_jours - 1} for simulation {simulation_id}: "
            f"got {jours}"
        )


def _simulation_from_rows(
    row: SimulationTable,
    daily_rows: list[DonneeJournaliereTable],
    tranche_rows: list[TrancheTable],
    arret_rows: list[ArretTable],
    modulation_rows: list[ModulationTable],
) -> Simulation:
    _check_daily_rows(
        daily_rows,
        row.horizon_jours,
        row.simulation_id,
    )

    arrets: dict[str, list[Arret]] = defaultdict(list)
    for arret_row in arret_rows:
        arrets[arret_row.tranche_id].append(
            Arret(
                type_arret=arret_row.type_arret,
                jour_debut=arret_row.jour_debut,
                jour_fin=arret_row.jour_fin,
            )
        )

    modulations: dict[str, list[Modulation]] = defaultdict(list)
    for modulation_row in modulation_rows:
        modulations[modulation_row.tranche_id].append(
            Modulation(
                jour_debut=modulation_row.jour_debut,
                jour_fin=modulation_row.jour_fin,
                facteur=modulation_row.facteur,
            )
        )

    return Simulation(
        simulation_id=row.simulation_id,
        nom=row.nom,
        cree_le=row.cree_le,
        horizon_jours=row.horizon_jours,
        prix_spot_eur_mwh=[daily_row.prix_spot_eur_mwh for daily_row in daily_rows],
        demande_nationale_mwh=[
            daily_row.demande_nationale_mwh for daily_row in daily_rows
        ],
        valeur_usage_eur_mwh=[
            daily_row.valeur_usage_eur_mwh for daily_row in daily_rows
        ],
        tranches=[
            SimulationTranche(
                tranche=Tranche(
                    identifiant=tranche_row.identifiant,
                    code_eic=tranche_row.code_eic,
                    puissance_nominale_mw=tranche_row.puissance_nominale_mw,
                    jepp_initial=tranche_row.jepp_initial,
                ),
                arrets=arrets.get(tranche_row.identifiant, []),
                modulations=modulations.get(tranche_row.identifiant, []),
            )
            for tranche_row in tranche_rows
        ],
    )


def list_simulations(session: Session) -> list[SimulationResume]:
    """Renvoie le résumé de toutes les simulations persistées."""
    rows = session.exec(
        select(SimulationTable).order_by(
            "cree_le",
            "simulation_id",
        )
    ).all()

    summaries: list[SimulationResume] = []
    for row in rows:
        nombre_tranches = session.scalar(
            select(func.count())
            .select_from(TrancheTable)
            .where(TrancheTable.simulation_id == row.simulation_id)
        )
        summaries.append(
            SimulationResume(
                simulation_id=row.simulation_id,
                nom=row.nom,
                cree_le=row.cree_le,
                horizon_jours=row.horizon_jours,
                nombre_tranches=int(nombre_tranches or 0),
            )
        )
    return summaries


def create_simulation(
    session: Session,
    payload: SimulationCreation,
) -> Simulation:
    """Crée une simulation complète et la renvoie."""
    simulation = Simulation(
        simulation_id=uuid4(),
        nom=payload.nom,
        cree_le=datetime.now(UTC),
        horizon_jours=payload.horizon_jours,
        prix_spot_eur_mwh=list(payload.prix_spot_eur_mwh),
        demande_nationale_mwh=list(payload.demande_nationale_mwh),
        valeur_usage_eur_mwh=list(payload.valeur_usage_eur_mwh),
        tranches=list(payload.tranches),
    )
    return _persist(session, simulation)


def get_simulation(
    session: Session,
    simulation_id: UUID,
) -> Simulation | None:
    """Charge et reconstruit une simulation complète, ou ``None``."""
    row = session.get(SimulationTable, simulation_id)
    if row is None:
        return None

    daily_rows = list(
        session.exec(
            select(DonneeJournaliereTable)
            .where(DonneeJournaliereTable.simulation_id == simulation_id)
            .order_by("jour")
        ).all()
    )
    tranche_rows = list(
        session.exec(
            select(TrancheTable)
            .where(TrancheTable.simulation_id == simulation_id)
            .order_by("identifiant")
        ).all()
    )
    arret_rows = list(
        session.exec(
            select(ArretTable)
            .where(ArretTable.simulation_id == simulation_id)
            .order_by("jour_debut", "id")
        ).all()
    )
    modulation_rows = list(
        session.exec(
            select(ModulationTable)
            .where(ModulationTable.simulation_id == simulation_id)
            .order_by("jour_debut", "id")
        ).all()
    )

    return _simulation_from_rows(
        row,
        daily_rows,
        tranche_rows,
        arret_rows,
        modulation_rows,
    )


def update_simulation(
    session: Session,
    simulation_id: UUID,
    payload: ParametresSimulation,
) -> Simulation | None:
    """Remplace le nom, l'horizon et les séries nationales."""
    simulation = get_simulation(session, simulation_id)
    if simulation is None:
        return None

    updated = Simulation(
        simulation_id=simulation.simulation_id,
        nom=payload.nom,
        cree_le=simulation.cree_le,
        horizon_jours=payload.horizon_jours,
        prix_spot_eur_mwh=list(payload.prix_spot_eur_mwh),
        demande_nationale_mwh=list(payload.demande_nationale_mwh),
        valeur_usage_eur_mwh=list(payload.valeur_usage_eur_mwh),
        tranches=list(simulation.tranches),
    )
    return _replace(session, updated)


def update_tranche(
    session: Session,
    simulation_id: UUID,
    plant_id: str,
    payload: ConfigurationTranche,
) -> Simulation | None:
    """Remplace la configuration d'une tranche sans changer son identifiant."""
    simulation = get_simulation(session, simulation_id)
    if simulation is None:
        return None
    if plant_id not in {entry.tranche.identifiant for entry in simulation.tranches}:
        return None

    tranches = [
        SimulationTranche(
            tranche=Tranche(
                identifiant=entry.tranche.identifiant,
                code_eic=payload.code_eic,
                puissance_nominale_mw=payload.puissance_nominale_mw,
                jepp_initial=payload.jepp_initial,
            ),
            arrets=list(entry.arrets),
            modulations=list(entry.modulations),
        )
        if entry.tranche.identifiant == plant_id
        else SimulationTranche(
            tranche=entry.tranche,
            arrets=list(entry.arrets),
            modulations=list(entry.modulations),
        )
        for entry in simulation.tranches
    ]

    updated = Simulation(
        simulation_id=simulation.simulation_id,
        nom=simulation.nom,
        cree_le=simulation.cree_le,
        horizon_jours=simulation.horizon_jours,
        prix_spot_eur_mwh=list(simulation.prix_spot_eur_mwh),
        demande_nationale_mwh=list(simulation.demande_nationale_mwh),
        valeur_usage_eur_mwh=list(simulation.valeur_usage_eur_mwh),
        tranches=tranches,
    )
    return _replace(session, updated)


def add_tranche(
    session: Session,
    simulation_id: UUID,
    payload: SimulationTranche,
) -> Simulation | None:
    """Ajoute une tranche à une simulation existante."""
    simulation = get_simulation(session, simulation_id)
    if simulation is None:
        return None

    updated = Simulation(
        simulation_id=simulation.simulation_id,
        nom=simulation.nom,
        cree_le=simulation.cree_le,
        horizon_jours=simulation.horizon_jours,
        prix_spot_eur_mwh=list(simulation.prix_spot_eur_mwh),
        demande_nationale_mwh=list(simulation.demande_nationale_mwh),
        valeur_usage_eur_mwh=list(simulation.valeur_usage_eur_mwh),
        tranches=[*simulation.tranches, payload],
    )
    return _replace(session, updated)


def _with_schedule(
    simulation: Simulation,
    plant_id: str,
    arrets: list[Arret] | None,
    modulations: list[Modulation] | None,
) -> Simulation | None:
    if plant_id not in {entry.tranche.identifiant for entry in simulation.tranches}:
        return None

    tranches = [
        SimulationTranche(
            tranche=entry.tranche,
            arrets=(
                list(arrets)
                if arrets is not None and entry.tranche.identifiant == plant_id
                else list(entry.arrets)
            ),
            modulations=(
                list(modulations)
                if modulations is not None and entry.tranche.identifiant == plant_id
                else list(entry.modulations)
            ),
        )
        for entry in simulation.tranches
    ]

    return Simulation(
        simulation_id=simulation.simulation_id,
        nom=simulation.nom,
        cree_le=simulation.cree_le,
        horizon_jours=simulation.horizon_jours,
        prix_spot_eur_mwh=list(simulation.prix_spot_eur_mwh),
        demande_nationale_mwh=list(simulation.demande_nationale_mwh),
        valeur_usage_eur_mwh=list(simulation.valeur_usage_eur_mwh),
        tranches=tranches,
    )


def replace_arrets(
    session: Session,
    simulation_id: UUID,
    plant_id: str,
    arrets: list[Arret],
) -> Simulation | None:
    """Remplace les arrêts d'une tranche, puis persiste la simulation."""
    simulation = get_simulation(session, simulation_id)
    if simulation is None:
        return None
    updated = _with_schedule(simulation, plant_id, arrets, None)
    if updated is None:
        return None
    return _replace(session, updated)


def replace_modulations(
    session: Session,
    simulation_id: UUID,
    plant_id: str,
    modulations: list[Modulation],
) -> Simulation | None:
    """Remplace les modulations d'une tranche, puis persiste la simulation."""
    simulation = get_simulation(session, simulation_id)
    if simulation is None:
        return None
    updated = _with_schedule(simulation, plant_id, None, modulations)
    if updated is None:
        return None
    return _replace(session, updated)


def delete_simulation(session: Session, simulation_id: UUID) -> bool:
    """Supprime une simulation et ses dépendances."""
    row = session.get(SimulationTable, simulation_id)
    if row is None:
        return False
    session.delete(row)
    session.commit()
    return True


def _duplicate_name(name: str) -> str:
    suffix = " (copie)"
    return f"{name[: 200 - len(suffix)]}{suffix}"


def duplicate_simulation(
    session: Session,
    simulation_id: UUID,
) -> Simulation | None:
    """Duplique une simulation avec un nouvel identifiant et un nom suffixé."""
    original = get_simulation(session, simulation_id)
    if original is None:
        return None

    duplicate = Simulation(
        simulation_id=uuid4(),
        nom=_duplicate_name(original.nom),
        cree_le=datetime.now(UTC),
        horizon_jours=original.horizon_jours,
        prix_spot_eur_mwh=list(original.prix_spot_eur_mwh),
        demande_nationale_mwh=list(original.demande_nationale_mwh),
        valeur_usage_eur_mwh=list(original.valeur_usage_eur_mwh),
        tranches=[
            SimulationTranche(
                tranche=entry.tranche,
                arrets=list(entry.arrets),
                modulations=list(entry.modulations),
            )
            for entry in original.tranches
        ],
    )
    return _persist(session, duplicate)
