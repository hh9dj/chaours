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


class TypeArret(str, Enum):
    """Type d'arrêt de tranche.

    - ``ASR`` : arrêt simple pour rechargement.
    - ``VP`` : visite partielle.
    - ``VD`` : visite décennale.
    """

    ASR = "ASR"
    VP = "VP"
    VD = "VD"


class TypeAlerte(str, Enum):
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


class _DomainModel(BaseModel):
    """Base des modèles métier mutables et stricts."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _ensure_finite(values: Sequence[float], field_name: str) -> None:
    for index, value in enumerate(values):
        if not math.isfinite(value):
            raise ValueError(f"{field_name}[{index}] must be finite")


class Tranche(_DomainModel):
    """Configuration statique d'une tranche nucléaire.

    - ``identifiant`` : identifiant interne de la tranche.
    - ``code_eic`` : code EIC européen.
    - ``puissance_nominale_mw`` : puissance électrique nominale en MW.
    - ``jepp_initial`` : stock de combustible initial en JEPP.
    """

    identifiant: str = Field(min_length=1)
    code_eic: str = Field(min_length=1)
    puissance_nominale_mw: float = Field(gt=0.0)
    jepp_initial: float = Field(ge=0.0)


class Arret(_DomainModel):
    """Arrêt de maintenance planifié pour une tranche.

    - ``type_arret`` : type d'arrêt (``ASR``, ``VP`` ou ``VD``).
    - ``jour_debut`` : premier jour de l'arrêt, inclus.
    - ``jour_fin`` : premier jour après l'arrêt, exclu.
    """

    type_arret: TypeArret
    jour_debut: int = Field(ge=0)
    jour_fin: int = Field(ge=1)

    @model_validator(mode="after")
    def _fin_after_debut(self) -> Self:
        if self.jour_fin <= self.jour_debut:
            raise ValueError("jour_fin must be greater than jour_debut")
        return self


class Modulation(_DomainModel):
    """Fenêtre de modulation manuelle imposée par l'utilisateur.

    - ``jour_debut`` : premier jour de la modulation, inclus.
    - ``jour_fin`` : premier jour après la modulation, exclu.
    - ``facteur`` : facteur de charge cible entre ``0.0`` et ``1.0``.
    """

    jour_debut: int = Field(ge=0)
    jour_fin: int = Field(ge=1)
    facteur: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _fin_after_debut(self) -> Self:
        if self.jour_fin <= self.jour_debut:
            raise ValueError("jour_fin must be greater than jour_debut")
        return self


def _validate_no_overlap(
    windows: Sequence[Arret | Modulation],
    label: str,
) -> None:
    ordered = sorted(windows, key=lambda window: window.jour_debut)
    for previous, current in zip(ordered, ordered[1:]):
        if current.jour_debut < previous.jour_fin:
            raise ValueError(
                f"overlapping {label} windows: "
                f"[{previous.jour_debut}, {previous.jour_fin}) and "
                f"[{current.jour_debut}, {current.jour_fin})"
            )


class SimulationTranche(_DomainModel):
    """Entrée de simulation d'une tranche nucléaire.

    - ``tranche`` : configuration statique de la tranche.
    - ``arrets`` : arrêts planifiés de cette tranche.
    - ``modulations`` : modulations manuelles de cette tranche.
    """

    tranche: Tranche
    arrets: list[Arret] = Field(default_factory=list)
    modulations: list[Modulation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _schedules_do_not_overlap(self) -> Self:
        _validate_no_overlap(self.arrets, "arrêt")
        _validate_no_overlap(self.modulations, "modulation")
        return self


class Simulation(_DomainModel):
    """Entrée complète d'une simulation.

    - ``simulation_id`` : identifiant de la simulation.
    - ``nom`` : nom lisible de la simulation.
    - ``cree_le`` : date de création en UTC.
    - ``horizon_jours`` : nombre de jours simulés.
    - ``prix_spot_eur_mwh`` : prix spot de longueur ``horizon_jours``,
      en €/MWh.
    - ``demande_nationale_mwh`` : demande nationale de longueur
      ``horizon_jours``, en MWh/jour.
    - ``valeur_usage_eur_mwh`` : valeur d'usage nationale de longueur
      ``horizon_jours``, en €/MWh.
    - ``tranches`` : tranches de la simulation, chacune avec ses arrêts et
      ses modulations.
    """

    simulation_id: UUID = Field(default_factory=uuid4)
    nom: str = Field(min_length=1, max_length=200)
    cree_le: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    horizon_jours: int = Field(ge=1, le=MAX_HORIZON_DAYS)
    prix_spot_eur_mwh: list[float]
    demande_nationale_mwh: list[float]
    valeur_usage_eur_mwh: list[float]
    tranches: list[SimulationTranche]

    @model_validator(mode="after")
    def _consistent_simulation(self) -> Self:
        tranche_ids = [entry.tranche.identifiant for entry in self.tranches]
        if len(tranche_ids) != len(set(tranche_ids)):
            raise ValueError("tranche identifiers must be unique")

        for field_name in (
            "prix_spot_eur_mwh",
            "demande_nationale_mwh",
            "valeur_usage_eur_mwh",
        ):
            values = getattr(self, field_name)
            if len(values) != self.horizon_jours:
                raise ValueError(
                    f"{field_name} length must equal horizon_jours: "
                    f"{len(values)} != {self.horizon_jours}"
                )
            _ensure_finite(values, field_name)

        if any(value < 0.0 for value in self.demande_nationale_mwh):
            raise ValueError("demande_nationale_mwh must be non-negative")

        for entry in self.tranches:
            for arret in entry.arrets:
                if arret.jour_fin > self.horizon_jours:
                    raise ValueError(
                        "arrêt window must be inside the horizon: "
                        f"[{arret.jour_debut}, {arret.jour_fin}) "
                        f"> {self.horizon_jours}"
                    )
            for modulation in entry.modulations:
                if modulation.jour_fin > self.horizon_jours:
                    raise ValueError(
                        "modulation window must be inside the horizon: "
                        f"[{modulation.jour_debut}, {modulation.jour_fin}) "
                        f"> {self.horizon_jours}"
                    )

        return self

    @property
    def arrets_par_tranche(self) -> dict[str, tuple[Arret, ...]]:
        """Renvoie les arrêts de chaque tranche, indexés par identifiant."""
        return {
            entry.tranche.identifiant: tuple(entry.arrets)
            for entry in self.tranches
        }

    @property
    def modulations_par_tranche(
        self,
    ) -> dict[str, tuple[Modulation, ...]]:
        """Renvoie les modulations de chaque tranche, par identifiant."""
        return {
            entry.tranche.identifiant: tuple(entry.modulations)
            for entry in self.tranches
        }


class SimulationResume(_DomainModel):
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


class SimulationCreation(_DomainModel):
    """Charge utile de création d'une simulation."""

    nom: str = Field(min_length=1, max_length=200)
    horizon_jours: int = Field(ge=1, le=MAX_HORIZON_DAYS)
    prix_spot_eur_mwh: list[float]
    demande_nationale_mwh: list[float]
    valeur_usage_eur_mwh: list[float]
    tranches: list[SimulationTranche]


class ParametresSimulation(_DomainModel):
    """Charge utile de mise à jour des paramètres d'une simulation."""

    nom: str = Field(min_length=1, max_length=200)
    horizon_jours: int = Field(ge=1, le=MAX_HORIZON_DAYS)
    prix_spot_eur_mwh: list[float]
    demande_nationale_mwh: list[float]
    valeur_usage_eur_mwh: list[float]


class ConfigurationTranche(_DomainModel):
    """Charge utile de mise à jour de la configuration d'une tranche."""

    code_eic: str = Field(min_length=1)
    puissance_nominale_mw: float = Field(gt=0.0)
    jepp_initial: float = Field(ge=0.0)


class ResultatTranche(_DomainModel):
    """Trajectoire calculée pour une tranche.

    - ``tranche_id`` : identifiant de la tranche.
    - ``facteurs_production`` : facteurs de charge physiquement contraints,
      de longueur ``horizon_jours``, entre ``0.0`` et ``1.0``.
    - ``energie_mwh`` : énergie journalière de longueur ``horizon_jours``,
      en MWh/jour.
    - ``jepp_restant`` : stock en fin de journée, de longueur
      ``horizon_jours``, en JEPP, borné à ``0``.
    - ``jours_epuisement`` : premier jour limité par le stock de chaque
      cycle concerné, par ordre croissant.
    """

    tranche_id: str = Field(min_length=1)
    facteurs_production: list[float]
    energie_mwh: list[float]
    jepp_restant: list[float]
    jours_epuisement: list[int]

    @field_validator("facteurs_production")
    @classmethod
    def _valid_production_factors(cls, values: list[float]) -> list[float]:
        _ensure_finite(values, "facteurs_production")
        if any(value < 0.0 or value > 1.0 for value in values):
            raise ValueError(
                "facteurs_production must be between 0.0 and 1.0"
            )
        return values

    @field_validator("energie_mwh", "jepp_restant")
    @classmethod
    def _finite_non_negative(cls, values: list[float]) -> list[float]:
        _ensure_finite(values, "energie_mwh/jepp_restant")
        if any(value < 0.0 for value in values):
            raise ValueError(
                "energie_mwh and jepp_restant must be non-negative"
            )
        return values

    @field_validator("jours_epuisement")
    @classmethod
    def _ascending_depletion_days(cls, values: list[int]) -> list[int]:
        if values != sorted(values):
            raise ValueError("jours_epuisement must be ascending")
        return values

    @model_validator(mode="after")
    def _arrays_share_horizon(self) -> Self:
        lengths = {
            len(self.facteurs_production),
            len(self.energie_mwh),
            len(self.jepp_restant),
        }
        if len(lengths) != 1:
            raise ValueError("result arrays must share the same length")
        return self


class Alerte(_DomainModel):
    """Alerte réglementaire ou physique.

    - ``type_alerte`` : famille d'alerte.
    - ``jour`` : jour concerné, ou ``None`` pour une alerte sans jour.
    - ``tranche_id`` : tranche concernée, ou ``None`` pour une alerte
      nationale.
    - ``message`` : texte destiné à l'interface, en français.
    """

    type_alerte: TypeAlerte
    jour: int | None
    tranche_id: str | None
    message: str


class ResultatSimulation(_DomainModel):
    """Sortie complète d'une simulation.

    - ``simulation_id`` : identifiant de la simulation exécutée.
    - ``duree_execution_ms`` : durée d'exécution du moteur, en millisecondes.
    - ``tranches`` : une trajectoire par tranche.
    - ``offre_nationale_mwh`` : offre nationale agrégée de longueur
      ``horizon_jours``, en MWh/jour.
    - ``demande_mwh`` : demande nationale de longueur ``horizon_jours``,
      en MWh/jour.
    - ``jours_deficit`` : indices des jours en déficit.
    - ``alertes`` : alertes produites par le moteur, dans un ordre
      déterministe : neutroniques, REMIT, déficits, puis prix spot sous la
      valeur d'usage.
    """

    simulation_id: UUID
    duree_execution_ms: float = Field(ge=0.0)
    tranches: list[ResultatTranche]
    offre_nationale_mwh: list[float]
    demande_mwh: list[float]
    jours_deficit: list[int]
    alertes: list[Alerte]

    @field_validator("offre_nationale_mwh", "demande_mwh")
    @classmethod
    def _finite_supply_and_demand(cls, values: list[float]) -> list[float]:
        _ensure_finite(values, "offre_nationale_mwh/demande_mwh")
        return values

    @model_validator(mode="after")
    def _consistent_result(self) -> Self:
        horizon = len(self.demande_mwh)
        if len(self.offre_nationale_mwh) != horizon:
            raise ValueError(
                "offre_nationale_mwh length must equal demande_mwh length"
            )

        tranche_ids = [resultat.tranche_id for resultat in self.tranches]
        if len(tranche_ids) != len(set(tranche_ids)):
            raise ValueError("tranche identifiers must be unique")

        for resultat in self.tranches:
            if len(resultat.facteurs_production) != horizon:
                raise ValueError(
                    f"facteurs_production length must equal horizon for "
                    f"{resultat.tranche_id!r}"
                )
            if len(resultat.energie_mwh) != horizon:
                raise ValueError(
                    f"energie_mwh length must equal horizon for "
                    f"{resultat.tranche_id!r}"
                )
            if len(resultat.jepp_restant) != horizon:
                raise ValueError(
                    f"jepp_restant length must equal horizon for "
                    f"{resultat.tranche_id!r}"
                )
            for day in resultat.jours_epuisement:
                if day < 0 or day >= horizon:
                    raise ValueError(
                        f"depletion day {day} outside horizon {horizon}"
                    )

        for day in self.jours_deficit:
            if day < 0 or day >= horizon:
                raise ValueError(
                    f"deficit day {day} outside horizon {horizon}"
                )

        for alerte in self.alertes:
            if alerte.jour is not None and (
                alerte.jour < 0 or alerte.jour >= horizon
            ):
                raise ValueError(
                    f"alert day {alerte.jour} outside horizon {horizon}"
                )

        return self

    @property
    def alertes_par_tranche(self) -> dict[str, tuple[Alerte, ...]]:
        """Renvoie les alertes de chaque tranche, par identifiant."""
        grouped: dict[str, list[Alerte]] = {
            resultat.tranche_id: [] for resultat in self.tranches
        }
        for alerte in self.alertes:
            if alerte.tranche_id is not None:
                grouped.setdefault(alerte.tranche_id, []).append(alerte)
        return {
            tranche_id: tuple(items) for tranche_id, items in grouped.items()
        }

    @property
    def alertes_nationales(self) -> tuple[Alerte, ...]:
        """Renvoie les alertes qui ne visent aucune tranche."""
        return tuple(
            alerte for alerte in self.alertes if alerte.tranche_id is None
        )
