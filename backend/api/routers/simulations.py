from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from api.schemas import (
    ConfigurationTranche,
    ParametresSimulation,
    SimulationCreation,
    SimulationResume,
)
from core.engine.pipeline import SimulationEngine
from core.models import (
    Arret,
    Modulation,
    ResultatSimulation,
    Simulation,
    SimulationTranche,
)
from db.database import get_session
from db.repository import SimulationRepository
from services.simulations import SimulationService


def get_simulation_service(
    session: Annotated[Session, Depends(get_session)],
) -> SimulationService:
    """Construit le service des simulations pour la requête courante."""
    return SimulationService(SimulationRepository(session), SimulationEngine())


SimulationServiceDep = Annotated[
    SimulationService,
    Depends(get_simulation_service),
]

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.get("/", response_model=list[SimulationResume])
def list_simulations(
    service: SimulationServiceDep,
) -> list[SimulationResume]:
    """Renvoie le résumé de toutes les simulations."""
    return service.list_all()


@router.post(
    "/",
    response_model=Simulation,
    status_code=status.HTTP_201_CREATED,
)
def create_simulation(
    payload: SimulationCreation,
    service: SimulationServiceDep,
) -> Simulation:
    """Crée une simulation avec un identifiant généré par le serveur."""
    return service.create(payload)


@router.get("/{simulation_id}", response_model=Simulation)
def get_simulation(
    simulation_id: UUID,
    service: SimulationServiceDep,
) -> Simulation:
    """Renvoie une simulation complète."""
    return service.get(simulation_id)


@router.put("/{simulation_id}", response_model=Simulation)
def update_simulation(
    simulation_id: UUID,
    payload: ParametresSimulation,
    service: SimulationServiceDep,
) -> Simulation:
    """Met à jour le nom, l'horizon et les séries nationales."""
    return service.update(simulation_id, payload)


@router.delete(
    "/{simulation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_simulation(
    simulation_id: UUID,
    service: SimulationServiceDep,
) -> Response:
    """Supprime une simulation et ses dépendances."""
    service.delete(simulation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{simulation_id}/plants",
    response_model=Simulation,
    status_code=status.HTTP_201_CREATED,
)
def add_tranche(
    simulation_id: UUID,
    payload: SimulationTranche,
    service: SimulationServiceDep,
) -> Simulation:
    """Ajoute une tranche à une simulation existante."""
    return service.add_tranche(simulation_id, payload)


@router.put(
    "/{simulation_id}/plants/{plant_id}",
    response_model=Simulation,
)
def update_tranche(
    simulation_id: UUID,
    plant_id: str,
    payload: ConfigurationTranche,
    service: SimulationServiceDep,
) -> Simulation:
    """Met à jour la configuration d'une tranche."""
    return service.update_tranche(simulation_id, plant_id, payload)


@router.put(
    "/{simulation_id}/plants/{plant_id}/maintenances",
    response_model=Simulation,
)
def update_arrets(
    simulation_id: UUID,
    plant_id: str,
    arrets: list[Arret],
    service: SimulationServiceDep,
) -> Simulation:
    """Remplace les arrêts d'une tranche."""
    return service.replace_arrets(simulation_id, plant_id, arrets)


@router.put(
    "/{simulation_id}/plants/{plant_id}/modulations",
    response_model=Simulation,
)
def update_modulations(
    simulation_id: UUID,
    plant_id: str,
    modulations: list[Modulation],
    service: SimulationServiceDep,
) -> Simulation:
    """Remplace les modulations d'une tranche."""
    return service.replace_modulations(simulation_id, plant_id, modulations)


@router.post(
    "/{simulation_id}/run",
    response_model=ResultatSimulation,
)
def run_simulation(
    simulation_id: UUID,
    service: SimulationServiceDep,
) -> ResultatSimulation:
    """Exécute le moteur sur la simulation persistée."""
    return service.run(simulation_id)
