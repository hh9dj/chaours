from datetime import datetime
from uuid import UUID

from pydantic import Field

from core.models import MAX_HORIZON_DAYS, DomainModel, SimulationTranche


class SimulationResume(DomainModel):
    """Résumé d'une simulation persistée.

    - ``simulation_id`` : identifiant de la simulation.
    - ``nom`` : nom lisible.
    - ``cree_le`` : date de création.
    - ``horizon_jours`` : nombre de jours simulés.
    - ``nombre_tranches`` : nombre de tranches.
    """

    simulation_id: UUID
    nom: str
    cree_le: datetime
    horizon_jours: int
    nombre_tranches: int


class SimulationCreation(DomainModel):
    """Charge utile de création d'une simulation."""

    nom: str = Field(min_length=1, max_length=200)
    horizon_jours: int = Field(ge=1, le=MAX_HORIZON_DAYS)
    prix_spot_eur_mwh: list[float]
    demande_nationale_mwh: list[float]
    valeur_usage_eur_mwh: list[float]
    tranches: list[SimulationTranche]


class ParametresSimulation(DomainModel):
    """Charge utile de mise à jour des paramètres d'une simulation."""

    nom: str = Field(min_length=1, max_length=200)
    horizon_jours: int = Field(ge=1, le=MAX_HORIZON_DAYS)
    prix_spot_eur_mwh: list[float]
    demande_nationale_mwh: list[float]
    valeur_usage_eur_mwh: list[float]


class ConfigurationTranche(DomainModel):
    """Charge utile de mise à jour de la configuration d'une tranche."""

    code_eic: str = Field(min_length=1)
    puissance_nominale_mw: float = Field(gt=0.0)
    jepp_initial: float = Field(ge=0.0)
