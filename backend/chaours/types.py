from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime, timezone
from enum import Enum
from typing import Self
from uuid import UUID, uuid4

import numpy as np
from numpy.typing import NDArray
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]
IntArray = NDArray[np.intp]

MAX_HORIZON_DAYS = 7305


class OutageKind(str, Enum):
    """Type d'arrêt de tranche.

    - ``ASR`` : arrêt simple pour rechargement.
    - ``VP`` : visite partielle.
    - ``VD`` : visite décennale.
    """

    ASR = "ASR"
    VP = "VP"
    VD = "VD"


class AlertKind(str, Enum):
    """Famille d'alerte produite par le moteur.

    - ``NEUTRONIC_ANOMALY`` : stock épuisé avant l'arrêt prévu.
    - ``REMIT_UMM`` : variation de puissance au-dessus du seuil REMIT.
    - ``RTE_DEFICIT`` : offre nationale insuffisante face à la demande.
    - ``SPOT_BELOW_USAGE_VALUE`` : prix spot inférieur à la valeur d'usage.
    """

    NEUTRONIC_ANOMALY = "NEUTRONIC_ANOMALY"
    REMIT_UMM = "REMIT_UMM"
    RTE_DEFICIT = "RTE_DEFICIT"
    SPOT_BELOW_USAGE_VALUE = "SPOT_BELOW_USAGE_VALUE"


class Severity(str, Enum):
    """Niveau de gravité d'une alerte."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class _DomainModel(BaseModel):
    """Base des modèles métier mutables et stricts."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _ensure_finite(values: Sequence[float], field_name: str) -> None:
    for index, value in enumerate(values):
        if not math.isfinite(value):
            raise ValueError(f"{field_name}[{index}] must be finite")


class Plant(_DomainModel):
    """Configuration statique d'une tranche nucléaire.

    - ``id`` : identifiant interne de la tranche.
    - ``eic_code`` : code EIC européen.
    - ``nominal_power_mw`` : puissance électrique nominale en MW.
    - ``initial_jepp`` : stock de combustible initial en JEPP.
    """

    id: str = Field(min_length=1)
    eic_code: str = Field(min_length=1)
    nominal_power_mw: float = Field(gt=0.0)
    initial_jepp: float = Field(ge=0.0)


class Maintenance(_DomainModel):
    """Arrêt de maintenance planifié pour une tranche.

    - ``kind`` : type d'arrêt (``ASR``, ``VP`` ou ``VD``).
    - ``start_day`` : premier jour de l'arrêt, inclus.
    - ``end_day`` : premier jour après l'arrêt, exclu.
    """

    kind: OutageKind
    start_day: int = Field(ge=0)
    end_day: int = Field(ge=1)

    @model_validator(mode="after")
    def _end_after_start(self) -> Self:
        if self.end_day <= self.start_day:
            raise ValueError("end_day must be greater than start_day")
        return self


class Modulation(_DomainModel):
    """Fenêtre de modulation manuelle imposée par l'utilisateur.

    - ``start_day`` : premier jour de la modulation, inclus.
    - ``end_day`` : premier jour après la modulation, exclu.
    - ``factor`` : facteur de charge cible entre ``0.0`` et ``1.0``.
    """

    start_day: int = Field(ge=0)
    end_day: int = Field(ge=1)
    factor: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _end_after_start(self) -> Self:
        if self.end_day <= self.start_day:
            raise ValueError("end_day must be greater than start_day")
        return self


def _validate_no_overlap(
    windows: Sequence[Maintenance | Modulation],
    label: str,
) -> None:
    ordered = sorted(windows, key=lambda window: window.start_day)
    for previous, current in zip(ordered, ordered[1:]):
        if current.start_day < previous.end_day:
            raise ValueError(
                f"overlapping {label} windows: "
                f"[{previous.start_day}, {previous.end_day}) and "
                f"[{current.start_day}, {current.end_day})"
            )


class Simulation(_DomainModel):
    """Tranche nucléaire avec ses arrêts et ses modulations.

    - ``plant`` : configuration statique de la tranche.
    - ``maintenances`` : arrêts planifiés de cette tranche.
    - ``modulations`` : modulations manuelles de cette tranche.
    """

    plant: Plant
    maintenances: list[Maintenance] = Field(default_factory=list)
    modulations: list[Modulation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _schedules_do_not_overlap(self) -> Self:
        _validate_no_overlap(self.maintenances, "maintenance")
        _validate_no_overlap(self.modulations, "modulation")
        return self


class Scenario(_DomainModel):
    """Entrée complète d'une simulation.

    - ``scenario_id`` : identifiant du scénario.
    - ``name`` : nom lisible du scénario.
    - ``created_at`` : date de création en UTC.
    - ``horizon_days`` : nombre de jours simulés.
    - ``spot_prices`` : prix spot de longueur ``horizon_days``, en €/MWh.
    - ``demand_mwh`` : demande nationale de longueur ``horizon_days``,
      en MWh/jour.
    - ``usage_values_eur_mwh`` : valeur d'usage en €/MWh, un scalaire
      statique par tranche, indexé par identifiant de tranche. Ce n'est pas
      une série journalière dans le MVP.
    - ``plants`` : tranches du scénario, chacune avec ses arrêts et ses
      modulations.
    """

    scenario_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=200)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    horizon_days: int = Field(ge=1, le=MAX_HORIZON_DAYS)
    spot_prices: list[float]
    demand_mwh: list[float]
    usage_values_eur_mwh: dict[str, float]
    plants: list[Simulation]

    @model_validator(mode="after")
    def _consistent_scenario(self) -> Self:
        if not self.plants:
            raise ValueError("scenario must contain at least one plant")

        plant_ids = [entry.plant.id for entry in self.plants]
        if len(plant_ids) != len(set(plant_ids)):
            raise ValueError("plant ids must be unique")

        if set(self.usage_values_eur_mwh) != set(plant_ids):
            raise ValueError(
                "usage_values_eur_mwh keys must exactly match plant ids"
            )

        if len(self.spot_prices) != self.horizon_days:
            raise ValueError(
                "spot_prices length must equal horizon_days: "
                f"{len(self.spot_prices)} != {self.horizon_days}"
            )
        if len(self.demand_mwh) != self.horizon_days:
            raise ValueError(
                "demand_mwh length must equal horizon_days: "
                f"{len(self.demand_mwh)} != {self.horizon_days}"
            )

        _ensure_finite(self.spot_prices, "spot_prices")
        _ensure_finite(self.demand_mwh, "demand_mwh")
        _ensure_finite(
            list(self.usage_values_eur_mwh.values()),
            "usage_values_eur_mwh",
        )

        if any(value < 0.0 for value in self.demand_mwh):
            raise ValueError("demand_mwh must be non-negative")

        for entry in self.plants:
            for maintenance in entry.maintenances:
                if maintenance.end_day > self.horizon_days:
                    raise ValueError(
                        "maintenance window must be inside the horizon: "
                        f"[{maintenance.start_day}, {maintenance.end_day}) "
                        f"> {self.horizon_days}"
                    )
            for modulation in entry.modulations:
                if modulation.end_day > self.horizon_days:
                    raise ValueError(
                        "modulation window must be inside the horizon: "
                        f"[{modulation.start_day}, {modulation.end_day}) "
                        f"> {self.horizon_days}"
                    )

        return self

    @property
    def maintenances_by_plant(
        self,
    ) -> dict[str, tuple[Maintenance, ...]]:
        """Renvoie les arrêts de chaque tranche, indexés par identifiant."""
        return {
            entry.plant.id: tuple(entry.maintenances) for entry in self.plants
        }

    @property
    def modulations_by_plant(
        self,
    ) -> dict[str, tuple[Modulation, ...]]:
        """Renvoie les modulations de chaque tranche, par identifiant."""
        return {
            entry.plant.id: tuple(entry.modulations) for entry in self.plants
        }


class PlantResult(_DomainModel):
    """Trajectoire calculée pour une tranche.

    - ``plant_id`` : identifiant de la tranche.
    - ``production_factors`` : facteurs de charge physiquement contraints,
      de longueur ``horizon_days``, entre ``0.0`` et ``1.0``. Ce ne sont pas
      les facteurs demandés : la limite physique du stock peut les réduire.
    - ``energy_mwh`` : énergie journalière de longueur ``horizon_days``,
      en MWh/jour.
    - ``remaining_jepp`` : stock en fin de journée, de longueur
      ``horizon_days``, en JEPP, borné à ``0``. Les rechargements sont
      reflétés aux points de recharge.
    - ``depletion_days`` : premier jour limité par le stock de chaque cycle
      concerné, par ordre croissant.
    """

    plant_id: str = Field(min_length=1)
    production_factors: list[float]
    energy_mwh: list[float]
    remaining_jepp: list[float]
    depletion_days: list[int]

    @field_validator("production_factors")
    @classmethod
    def _valid_production_factors(cls, values: list[float]) -> list[float]:
        _ensure_finite(values, "production_factors")
        if any(value < 0.0 or value > 1.0 for value in values):
            raise ValueError("production_factors must be between 0.0 and 1.0")
        return values

    @field_validator("energy_mwh", "remaining_jepp")
    @classmethod
    def _finite_non_negative(cls, values: list[float]) -> list[float]:
        _ensure_finite(values, "energy_mwh/remaining_jepp")
        if any(value < 0.0 for value in values):
            raise ValueError("energy_mwh and remaining_jepp must be non-negative")
        return values

    @field_validator("depletion_days")
    @classmethod
    def _ascending_depletion_days(cls, values: list[int]) -> list[int]:
        if values != sorted(values):
            raise ValueError("depletion_days must be ascending")
        return values

    @model_validator(mode="after")
    def _arrays_share_horizon(self) -> Self:
        lengths = {
            len(self.production_factors),
            len(self.energy_mwh),
            len(self.remaining_jepp),
        }
        if len(lengths) != 1:
            raise ValueError("result arrays must share the same length")
        return self


class Alert(_DomainModel):
    """Alerte réglementaire ou physique.

    - ``kind`` : famille d'alerte.
    - ``day`` : jour concerné, ou ``None`` pour une alerte sur un arrêt.
    - ``plant_id`` : tranche concernée, ou ``None`` pour une alerte nationale.
    - ``message`` : texte destiné à l'interface, en français.
    - ``severity`` : niveau de gravité.
    """

    kind: AlertKind
    day: int | None
    plant_id: str | None
    message: str
    severity: Severity


class SimulationResult(_DomainModel):
    """Sortie complète d'une simulation.

    - ``scenario_id`` : identifiant du scénario exécuté.
    - ``execution_time_ms`` : durée d'exécution du moteur, en millisecondes.
    - ``plants`` : une trajectoire par tranche.
    - ``national_supply_mwh`` : offre nationale agrégée de longueur
      ``horizon_days``, en MWh/jour.
    - ``demand_mwh`` : demande nationale de longueur ``horizon_days``,
      en MWh/jour.
    - ``deficit_days`` : indices des jours en déficit.
    - ``alerts`` : alertes produites par le moteur, dans un ordre
      déterministe : neutroniques, REMIT, déficits, puis prix spot sous la
      valeur d'usage.
    """

    scenario_id: UUID
    execution_time_ms: float = Field(ge=0.0)
    plants: list[PlantResult]
    national_supply_mwh: list[float]
    demand_mwh: list[float]
    deficit_days: list[int]
    alerts: list[Alert]

    @field_validator("national_supply_mwh", "demand_mwh")
    @classmethod
    def _finite_supply_and_demand(cls, values: list[float]) -> list[float]:
        _ensure_finite(values, "national_supply_mwh/demand_mwh")
        return values

    @model_validator(mode="after")
    def _consistent_result(self) -> Self:
        horizon = len(self.demand_mwh)
        if len(self.national_supply_mwh) != horizon:
            raise ValueError(
                "national_supply_mwh length must equal demand_mwh length"
            )

        plant_ids = [result.plant_id for result in self.plants]
        if len(plant_ids) != len(set(plant_ids)):
            raise ValueError("plant ids must be unique")

        for result in self.plants:
            if len(result.production_factors) != horizon:
                raise ValueError(
                    f"production_factors length must equal horizon for "
                    f"{result.plant_id!r}"
                )
            if len(result.energy_mwh) != horizon:
                raise ValueError(
                    f"energy_mwh length must equal horizon for "
                    f"{result.plant_id!r}"
                )
            if len(result.remaining_jepp) != horizon:
                raise ValueError(
                    f"remaining_jepp length must equal horizon for "
                    f"{result.plant_id!r}"
                )
            for day in result.depletion_days:
                if day < 0 or day >= horizon:
                    raise ValueError(
                        f"depletion day {day} outside horizon {horizon}"
                    )

        for day in self.deficit_days:
            if day < 0 or day >= horizon:
                raise ValueError(
                    f"deficit day {day} outside horizon {horizon}"
                )

        for alert in self.alerts:
            if alert.day is not None and (
                alert.day < 0 or alert.day >= horizon
            ):
                raise ValueError(
                    f"alert day {alert.day} outside horizon {horizon}"
                )

        return self

    @property
    def alerts_by_plant(self) -> dict[str, tuple[Alert, ...]]:
        """Renvoie les alertes de chaque tranche, indexées par identifiant."""
        grouped: dict[str, list[Alert]] = {
            result.plant_id: [] for result in self.plants
        }
        for alert in self.alerts:
            if alert.plant_id is not None:
                grouped.setdefault(alert.plant_id, []).append(alert)
        return {plant_id: tuple(items) for plant_id, items in grouped.items()}

    @property
    def national_alerts(self) -> tuple[Alert, ...]:
        """Renvoie les alertes qui ne visent aucune tranche."""
        return tuple(
            alert for alert in self.alerts if alert.plant_id is None
        )
