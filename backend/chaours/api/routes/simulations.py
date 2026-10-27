from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from chaours.api.deps import get_session
from chaours.db import repository
from chaours.engine import NucliEngine
from chaours.types import (
    Arret,
    ConfigurationTranche,
    Modulation,
    ParametresSimulation,
    ResultatSimulation,
    Simulation,
    SimulationCreation,
    SimulationResume,
    SimulationTranche,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.get("/", response_model=list[SimulationResume])
def list_simulations(
    session: Session = Depends(get_session),
) -> list[SimulationResume]:
    """Renvoie le résumé de toutes les simulations."""
    return repository.list_simulations(session)


@router.post(
    "/",
    response_model=Simulation,
    status_code=status.HTTP_201_CREATED,
)
def create_simulation(
    payload: SimulationCreation,
    session: Session = Depends(get_session),
) -> Simulation:
    """Crée une simulation avec un identifiant généré par le serveur."""
    return repository.create_simulation(session, payload)


@router.get("/{simulation_id}", response_model=Simulation)
def get_simulation(
    simulation_id: UUID,
    session: Session = Depends(get_session),
) -> Simulation:
    """Renvoie une simulation complète."""
    simulation = repository.get_simulation(session, simulation_id)
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation introuvable",
        )
    return simulation


@router.put("/{simulation_id}", response_model=Simulation)
def update_simulation(
    simulation_id: UUID,
    payload: ParametresSimulation,
    session: Session = Depends(get_session),
) -> Simulation:
    """Met à jour le nom, l'horizon et les séries nationales."""
    simulation = repository.update_simulation(
        session,
        simulation_id,
        payload,
    )
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation introuvable",
        )
    return simulation


@router.delete(
    "/{simulation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_simulation(
    simulation_id: UUID,
    session: Session = Depends(get_session),
) -> Response:
    """Supprime une simulation et ses dépendances."""
    if not repository.delete_simulation(session, simulation_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation introuvable",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{simulation_id}/plants",
    response_model=Simulation,
    status_code=status.HTTP_201_CREATED,
)
def add_tranche(
    simulation_id: UUID,
    payload: SimulationTranche,
    session: Session = Depends(get_session),
) -> Simulation:
    """Ajoute une tranche à une simulation existante."""
    simulation = repository.add_tranche(
        session,
        simulation_id,
        payload,
    )
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation introuvable",
        )
    return simulation


@router.put(
    "/{simulation_id}/plants/{plant_id}",
    response_model=Simulation,
)
def update_tranche(
    simulation_id: UUID,
    plant_id: str,
    payload: ConfigurationTranche,
    session: Session = Depends(get_session),
) -> Simulation:
    """Met à jour la configuration d'une tranche."""
    simulation = repository.update_tranche(
        session,
        simulation_id,
        plant_id,
        payload,
    )
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation ou tranche introuvable",
        )
    return simulation


@router.put(
    "/{simulation_id}/plants/{plant_id}/maintenances",
    response_model=Simulation,
)
def update_arrets(
    simulation_id: UUID,
    plant_id: str,
    arrets: list[Arret],
    session: Session = Depends(get_session),
) -> Simulation:
    """Remplace les arrêts d'une tranche."""
    simulation = repository.replace_arrets(
        session,
        simulation_id,
        plant_id,
        arrets,
    )
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation ou tranche introuvable",
        )
    return simulation


@router.put(
    "/{simulation_id}/plants/{plant_id}/modulations",
    response_model=Simulation,
)
def update_modulations(
    simulation_id: UUID,
    plant_id: str,
    modulations: list[Modulation],
    session: Session = Depends(get_session),
) -> Simulation:
    """Remplace les modulations d'une tranche."""
    simulation = repository.replace_modulations(
        session,
        simulation_id,
        plant_id,
        modulations,
    )
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation ou tranche introuvable",
        )
    return simulation


@router.post(
    "/{simulation_id}/run",
    response_model=ResultatSimulation,
)
def run_simulation(
    simulation_id: UUID,
    session: Session = Depends(get_session),
) -> ResultatSimulation:
    """Exécute le moteur sur la simulation persistée."""
    simulation = repository.get_simulation(session, simulation_id)
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation introuvable",
        )
    return NucliEngine().run(simulation)
