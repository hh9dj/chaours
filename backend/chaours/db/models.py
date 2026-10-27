from datetime import datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy import ForeignKeyConstraint, Index
from sqlmodel import Field, SQLModel

from chaours.types import TypeArret


class SimulationTable(SQLModel, table=True):
    """Ligne persistée de l'en-tête d'une simulation."""

    __tablename__: ClassVar[str] = "simulations"

    simulation_id: UUID = Field(primary_key=True)
    nom: str
    cree_le: datetime
    horizon_jours: int


class DonneeJournaliereTable(SQLModel, table=True):
    """Ligne persistée d'une série journalière nationale."""

    __tablename__: ClassVar[str] = "donnees_journalieres"

    simulation_id: UUID = Field(
        primary_key=True,
        foreign_key="simulations.simulation_id",
        ondelete="CASCADE",
    )
    jour: int = Field(primary_key=True)
    prix_spot_eur_mwh: float
    demande_nationale_mwh: float
    valeur_usage_eur_mwh: float


class TrancheTable(SQLModel, table=True):
    """Ligne persistée d'une tranche rattachée à une simulation."""

    __tablename__: ClassVar[str] = "tranches"

    simulation_id: UUID = Field(
        primary_key=True,
        foreign_key="simulations.simulation_id",
        ondelete="CASCADE",
    )
    identifiant: str = Field(primary_key=True)
    code_eic: str
    jepp_initial: float
    puissance_nominale_mw: float


class ArretTable(SQLModel, table=True):
    """Ligne persistée d'un arrêt planifié."""

    __tablename__: ClassVar[str] = "arrets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["simulation_id", "tranche_id"],
            ["tranches.simulation_id", "tranches.identifiant"],
            ondelete="CASCADE",
        ),
        Index(
            "ix_arrets_simulation_tranche",
            "simulation_id",
            "tranche_id",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    simulation_id: UUID
    tranche_id: str
    type_arret: TypeArret
    jour_debut: int
    jour_fin: int


class ModulationTable(SQLModel, table=True):
    """Ligne persistée d'une modulation manuelle."""

    __tablename__: ClassVar[str] = "modulations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["simulation_id", "tranche_id"],
            ["tranches.simulation_id", "tranches.identifiant"],
            ondelete="CASCADE",
        ),
        Index(
            "ix_modulations_simulation_tranche",
            "simulation_id",
            "tranche_id",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    simulation_id: UUID
    tranche_id: str
    jour_debut: int
    jour_fin: int
    facteur: float
