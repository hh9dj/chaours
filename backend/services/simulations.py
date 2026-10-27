from typing import NoReturn
from uuid import UUID

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
    SimulationNotFoundError,
    SimulationTranche,
    TrancheNotFoundError,
)
from db.repository import SimulationRepository


class SimulationService:
    """Cas d'usage liés aux simulations.

    Le service orchestre le repository et le moteur de calcul. Il traduit les
    absences de données métier en erreurs typées, que l'API convertit en
    réponses HTTP.
    """

    def __init__(
        self,
        repository: SimulationRepository,
        engine: SimulationEngine | None = None,
    ) -> None:
        self._repository = repository
        self._engine = engine or SimulationEngine()

    def list_all(self) -> list[SimulationResume]:
        """Renvoie le résumé de toutes les simulations."""
        return self._repository.list_all()

    def create(self, payload: SimulationCreation) -> Simulation:
        """Crée une simulation avec un identifiant généré par le serveur."""
        return self._repository.create(payload)

    def get(self, simulation_id: UUID) -> Simulation:
        """Renvoie une simulation complète, ou lève une erreur métier."""
        simulation = self._repository.get(simulation_id)
        if simulation is None:
            raise SimulationNotFoundError(simulation_id)
        return simulation

    def update(
        self,
        simulation_id: UUID,
        payload: ParametresSimulation,
    ) -> Simulation:
        """Met à jour le nom, l'horizon et les séries nationales."""
        simulation = self._repository.update(simulation_id, payload)
        if simulation is None:
            raise SimulationNotFoundError(simulation_id)
        return simulation

    def update_tranche(
        self,
        simulation_id: UUID,
        plant_id: str,
        payload: ConfigurationTranche,
    ) -> Simulation:
        """Met à jour la configuration d'une tranche."""
        simulation = self._repository.update_tranche(
            simulation_id,
            plant_id,
            payload,
        )
        if simulation is None:
            self._raise_absence(simulation_id, plant_id)
        return simulation

    def add_tranche(
        self,
        simulation_id: UUID,
        payload: SimulationTranche,
    ) -> Simulation:
        """Ajoute une tranche à une simulation existante."""
        simulation = self._repository.add_tranche(simulation_id, payload)
        if simulation is None:
            raise SimulationNotFoundError(simulation_id)
        return simulation

    def replace_arrets(
        self,
        simulation_id: UUID,
        plant_id: str,
        arrets: list[Arret],
    ) -> Simulation:
        """Remplace les arrêts d'une tranche."""
        simulation = self._repository.replace_arrets(
            simulation_id,
            plant_id,
            arrets,
        )
        if simulation is None:
            self._raise_absence(simulation_id, plant_id)
        return simulation

    def replace_modulations(
        self,
        simulation_id: UUID,
        plant_id: str,
        modulations: list[Modulation],
    ) -> Simulation:
        """Remplace les modulations d'une tranche."""
        simulation = self._repository.replace_modulations(
            simulation_id,
            plant_id,
            modulations,
        )
        if simulation is None:
            self._raise_absence(simulation_id, plant_id)
        return simulation

    def delete(self, simulation_id: UUID) -> None:
        """Supprime une simulation et ses dépendances."""
        if not self._repository.delete(simulation_id):
            raise SimulationNotFoundError(simulation_id)

    def run(self, simulation_id: UUID) -> ResultatSimulation:
        """Exécute le moteur sur la simulation persistée."""
        return self._engine.run(self.get(simulation_id))

    def _raise_absence(
        self,
        simulation_id: UUID,
        plant_id: str,
    ) -> NoReturn:
        if self._repository.get(simulation_id) is None:
            raise SimulationNotFoundError(simulation_id)
        raise TrancheNotFoundError(simulation_id, plant_id)
