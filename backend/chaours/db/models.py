from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from chaours.types import OutageKind


class ScenarioTable(SQLModel, table=True):
    """Ligne persistée d'un scénario complet."""

    __tablename__ = "scenarios"

    scenario_id: UUID = Field(primary_key=True)
    name: str
    created_at: datetime
    horizon_days: int
    spot_prices: list[float] = Field(
        sa_column=Column(JSON, nullable=False)
    )
    demand_mwh: list[float] = Field(
        sa_column=Column(JSON, nullable=False)
    )
    usage_values_eur_mwh: dict[str, float] = Field(
        sa_column=Column(JSON, nullable=False)
    )

    plants: list["PlantTable"] = Relationship(
        back_populates="scenario",
        cascade_delete=True,
    )


class PlantTable(SQLModel, table=True):
    """Ligne persistée d'une tranche rattachée à un scénario."""

    __tablename__ = "plants"
    __table_args__ = (
        UniqueConstraint(
            "scenario_id",
            "plant_id",
            name="uq_plants_scenario_plant",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    scenario_id: UUID = Field(
        foreign_key="scenarios.scenario_id",
        ondelete="CASCADE",
        index=True,
    )
    plant_id: str
    eic_code: str
    nominal_power_mw: float
    initial_jepp: float

    scenario: ScenarioTable | None = Relationship(back_populates="plants")
    maintenances: list["MaintenanceTable"] = Relationship(
        back_populates="plant",
        cascade_delete=True,
    )
    modulations: list["ModulationTable"] = Relationship(
        back_populates="plant",
        cascade_delete=True,
    )


class MaintenanceTable(SQLModel, table=True):
    """Ligne persistée d'un arrêt planifié."""

    __tablename__ = "maintenances"

    id: int | None = Field(default=None, primary_key=True)
    plant_id: int = Field(
        foreign_key="plants.id",
        ondelete="CASCADE",
        index=True,
    )
    kind: OutageKind
    start_day: int
    end_day: int

    plant: PlantTable | None = Relationship(back_populates="maintenances")


class ModulationTable(SQLModel, table=True):
    """Ligne persistée d'une modulation manuelle."""

    __tablename__ = "modulations"

    id: int | None = Field(default=None, primary_key=True)
    plant_id: int = Field(
        foreign_key="plants.id",
        ondelete="CASCADE",
        index=True,
    )
    start_day: int
    end_day: int
    factor: float

    plant: PlantTable | None = Relationship(back_populates="modulations")
