from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]
IntArray = NDArray[np.intp]


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


@dataclass(frozen=True)
class Plant:
    """Configuration statique d'une tranche nucléaire.

    - ``id`` : identifiant interne de la tranche.
    - ``eic_code`` : code EIC européen.
    - ``nominal_power_mw`` : puissance électrique nominale en MW.
    - ``initial_jepp`` : stock de combustible initial en JEPP.
    """

    id: str
    eic_code: str
    nominal_power_mw: float
    initial_jepp: float


@dataclass(frozen=True)
class Maintenance:
    """Arrêt de maintenance planifié pour une tranche.

    - ``kind`` : type d'arrêt (``ASR``, ``VP`` ou ``VD``).
    - ``start_day`` : premier jour de l'arrêt, inclus.
    - ``end_day`` : premier jour après l'arrêt, exclu.
    """

    kind: OutageKind
    start_day: int
    end_day: int


@dataclass(frozen=True)
class Modulation:
    """Fenêtre de modulation manuelle imposée par l'utilisateur.

    - ``start_day`` : premier jour de la modulation, inclus.
    - ``end_day`` : premier jour après la modulation, exclu.
    - ``factor`` : facteur de charge cible entre ``0.0`` et ``1.0``.
    """

    start_day: int
    end_day: int
    factor: float


@dataclass
class Simulation:
    """Tranche nucléaire avec ses arrêts et ses modulations.

    - ``plant`` : configuration statique de la tranche.
    - ``maintenances`` : arrêts planifiés de cette tranche.
    - ``modulations`` : modulations manuelles de cette tranche.

    Les listes sont mutables pour permettre la construction progressive du
    scénario. Elles appartiennent à cette instance et ne sont jamais partagées
    entre deux scénarios.
    """

    plant: Plant
    maintenances: list[Maintenance] = field(default_factory=list)
    modulations: list[Modulation] = field(default_factory=list)

    def add_maintenance(
        self,
        kind: OutageKind,
        start_day: int,
        end_day: int,
    ) -> Maintenance:
        """Ajoute un arrêt à cette tranche et le renvoie."""
        maintenance = Maintenance(kind, start_day, end_day)
        self.maintenances.append(maintenance)
        return maintenance

    def add_modulation(
        self,
        start_day: int,
        end_day: int,
        factor: float,
    ) -> Modulation:
        """Ajoute une modulation à cette tranche et la renvoie."""
        modulation = Modulation(start_day, end_day, factor)
        self.modulations.append(modulation)
        return modulation


@dataclass
class Scenario:
    """Entrée complète d'une simulation.

    - ``scenario_id`` : identifiant du scénario.
    - ``horizon_days`` : nombre de jours simulés.
    - ``spot_prices`` : prix spot de forme ``(horizon_days,)``, en €/MWh.
    - ``demand_mwh`` : demande nationale de forme ``(horizon_days,)``,
      en MWh/jour.
    - ``usage_values_eur_mwh`` : valeur d'usage en €/MWh, un scalaire
      statique par tranche, indexé par identifiant de tranche. Ce n'est pas
      une série journalière dans le MVP.
    - ``plants`` : tranches du scénario, chacune avec ses arrêts et ses
      modulations.

    Le scénario est mutable pour le POC : ses champs, sa liste de tranches
    et les listes de calendriers portées par chaque tranche peuvent être
    modifiés directement.
    """

    scenario_id: str
    horizon_days: int
    spot_prices: FloatArray
    demand_mwh: FloatArray
    usage_values_eur_mwh: dict[str, float]
    plants: list[Simulation] = field(default_factory=list)

    def add_plant(self, plant: Plant) -> Simulation:
        """Ajoute une tranche au scénario et renvoie son entrée."""
        entry = Simulation(plant)
        self.plants.append(entry)
        return entry

    @property
    def maintenances_by_plant(
        self,
    ) -> dict[str, tuple[Maintenance, ...]]:
        """Renvoie les arrêts de chaque tranche, indexés par identifiant."""
        return {entry.plant.id: tuple(entry.maintenances) for entry in self.plants}

    @property
    def modulations_by_plant(
        self,
    ) -> dict[str, tuple[Modulation, ...]]:
        """Renvoie les modulations de chaque tranche, par identifiant."""
        return {entry.plant.id: tuple(entry.modulations) for entry in self.plants}


@dataclass(frozen=True)
class PlantResult:
    """Trajectoire calculée pour une tranche.

    - ``plant_id`` : identifiant de la tranche.
    - ``production_factors`` : facteurs de charge physiquement contraints,
      de forme ``(horizon_days,)``, entre ``0.0`` et ``1.0``. Ce ne sont pas
      les facteurs demandés : la limite physique du stock peut les réduire.
    - ``energy_mwh`` : énergie journalière de forme ``(horizon_days,)``,
      en MWh/jour.
    - ``remaining_jepp`` : stock en fin de journée, de forme
      ``(horizon_days,)``, en JEPP, borné à ``0``. Les rechargements sont
      reflétés aux points de recharge.
    - ``depletion_days`` : premier jour limité par le stock de chaque cycle
      concerné, par ordre croissant.
    """

    plant_id: str
    production_factors: FloatArray
    energy_mwh: FloatArray
    remaining_jepp: FloatArray
    depletion_days: tuple[int, ...]


@dataclass(frozen=True)
class Alert:
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


@dataclass(frozen=True)
class SimulationResult:
    """Sortie complète d'une simulation.

    - ``scenario_id`` : identifiant du scénario exécuté.
    - ``execution_time_ms`` : durée d'exécution du moteur, en millisecondes.
    - ``plants`` : une trajectoire par tranche.
    - ``national_supply_mwh`` : offre nationale agrégée de forme
      ``(horizon_days,)``, en MWh/jour.
    - ``demand_mwh`` : demande nationale de forme ``(horizon_days,)``,
      en MWh/jour.
    - ``deficit_days`` : indices des jours en déficit.
    - ``alerts`` : alertes produites par le moteur, dans un ordre
      déterministe : neutroniques, REMIT, déficits, puis prix spot sous la
      valeur d'usage.
    """

    scenario_id: str
    execution_time_ms: float
    plants: tuple[PlantResult, ...]
    national_supply_mwh: FloatArray
    demand_mwh: FloatArray
    deficit_days: IntArray
    alerts: tuple[Alert, ...]
