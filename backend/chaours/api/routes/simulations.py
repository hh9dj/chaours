from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from chaours.api.deps import get_session
from chaours.db import repository
from chaours.engine import NucliEngine
from chaours.types import (
    Maintenance,
    Modulation,
    Scenario,
    SimulationResult,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post(
    "/",
    response_model=Scenario,
    status_code=status.HTTP_201_CREATED,
)
def create_simulation(
    scenario: Scenario,
    session: Session = Depends(get_session),
) -> Scenario:
    """Crée un scénario isolé avec un identifiant serveur."""
    scenario.scenario_id = uuid4()
    scenario.created_at = datetime.now(UTC)
    return repository.create_scenario(session, scenario)


@router.get("/{scenario_id}", response_model=Scenario)
def get_simulation(
    scenario_id: UUID,
    session: Session = Depends(get_session),
) -> Scenario:
    """Renvoie un scénario complet."""
    scenario = repository.get_scenario(session, scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )
    return scenario


@router.delete(
    "/{scenario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_simulation(
    scenario_id: UUID,
    session: Session = Depends(get_session),
) -> Response:
    """Supprime un scénario et ses dépendances."""
    if not repository.delete_scenario(session, scenario_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{scenario_id}/plants/{plant_id}/maintenances",
    response_model=Scenario,
)
def update_maintenances(
    scenario_id: UUID,
    plant_id: str,
    maintenances: list[Maintenance],
    session: Session = Depends(get_session),
) -> Scenario:
    """Remplace les arrêts d'une tranche et renvoie le scénario validé."""
    scenario = repository.replace_maintenances(
        session,
        scenario_id,
        plant_id,
        maintenances,
    )
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario or plant not found",
        )
    return scenario


@router.put(
    "/{scenario_id}/plants/{plant_id}/modulations",
    response_model=Scenario,
)
def update_modulations(
    scenario_id: UUID,
    plant_id: str,
    modulations: list[Modulation],
    session: Session = Depends(get_session),
) -> Scenario:
    """Remplace les modulations d'une tranche et renvoie le scénario validé."""
    scenario = repository.replace_modulations(
        session,
        scenario_id,
        plant_id,
        modulations,
    )
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario or plant not found",
        )
    return scenario


@router.post(
    "/{scenario_id}/run",
    response_model=SimulationResult,
)
def run_simulation(
    scenario_id: UUID,
    session: Session = Depends(get_session),
) -> SimulationResult:
    """Exécute le moteur sur le scénario persisté."""
    scenario = repository.get_scenario(session, scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )
    return NucliEngine().run(scenario)
