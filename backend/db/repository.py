from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlmodel import Session, select

from api.schemas import (
    ConfigurationTranche,
    ParametresSimulation,
    SimulationCreation,
    SimulationResume,
)
from core.models import (
    Arret,
    Modulation,
    Simulation,
    SimulationTranche,
    Tranche,
)
from db.tables import (
    ArretTable,
    DonneeJournaliereTable,
    ModulationTable,
    SimulationTable,
    TrancheTable,
)


class SimulationRepository:
    """Accès persistant aux simulations, lié à une session SQLModel."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _persist(self, simulation: Simulation) -> Simulation:
        self._session.add(
            SimulationTable(
                simulation_id=simulation.simulation_id,
                nom=simulation.nom,
                cree_le=simulation.cree_le,
                horizon_jours=simulation.horizon_jours,
            )
        )
        self._session.flush()

        for jour in range(simulation.horizon_jours):
            self._session.add(
                DonneeJournaliereTable(
                    simulation_id=simulation.simulation_id,
                    jour=jour,
                    prix_spot_eur_mwh=simulation.prix_spot_eur_mwh[jour],
                    demande_nationale_mwh=simulation.demande_nationale_mwh[jour],
                    valeur_usage_eur_mwh=simulation.valeur_usage_eur_mwh[jour],
                )
            )

        for entry in simulation.tranches:
            tranche_id = entry.tranche.identifiant
            self._session.add(
                TrancheTable(
                    simulation_id=simulation.simulation_id,
                    identifiant=tranche_id,
                    code_eic=entry.tranche.code_eic,
                    jepp_initial=entry.tranche.jepp_initial,
                    puissance_nominale_mw=entry.tranche.puissance_nominale_mw,
                )
            )
            self._session.flush()
            for arret in entry.arrets:
                self._session.add(
                    ArretTable(
                        simulation_id=simulation.simulation_id,
                        tranche_id=tranche_id,
                        type_arret=arret.type_arret,
                        jour_debut=arret.jour_debut,
                        jour_fin=arret.jour_fin,
                    )
                )
            for modulation in entry.modulations:
                self._session.add(
                    ModulationTable(
                        simulation_id=simulation.simulation_id,
                        tranche_id=tranche_id,
                        jour_debut=modulation.jour_debut,
                        jour_fin=modulation.jour_fin,
                        facteur=modulation.facteur,
                    )
                )

        self._session.commit()
        return simulation

    def _replace(self, simulation: Simulation) -> Simulation:
        existing = self._session.get(SimulationTable, simulation.simulation_id)
        if existing is not None:
            self._session.delete(existing)
            self._session.flush()
        self._session.expunge_all()
        return self._persist(simulation)

    def _with_schedule(
        self,
        simulation: Simulation,
        plant_id: str,
        arrets: list[Arret] | None,
        modulations: list[Modulation] | None,
    ) -> Simulation | None:
        if plant_id not in {entry.tranche.identifiant for entry in simulation.tranches}:
            return None

        tranches = [
            SimulationTranche(
                tranche=entry.tranche,
                arrets=(
                    list(arrets)
                    if arrets is not None and entry.tranche.identifiant == plant_id
                    else list(entry.arrets)
                ),
                modulations=(
                    list(modulations)
                    if modulations is not None and entry.tranche.identifiant == plant_id
                    else list(entry.modulations)
                ),
            )
            for entry in simulation.tranches
        ]

        return Simulation(
            simulation_id=simulation.simulation_id,
            nom=simulation.nom,
            cree_le=simulation.cree_le,
            horizon_jours=simulation.horizon_jours,
            prix_spot_eur_mwh=list(simulation.prix_spot_eur_mwh),
            demande_nationale_mwh=list(simulation.demande_nationale_mwh),
            valeur_usage_eur_mwh=list(simulation.valeur_usage_eur_mwh),
            tranches=tranches,
        )

    def list_all(self) -> list[SimulationResume]:
        """Renvoie le résumé de toutes les simulations persistées."""
        rows = self._session.exec(
            select(SimulationTable).order_by(
                "cree_le",
                "simulation_id",
            )
        ).all()

        summaries: list[SimulationResume] = []
        for row in rows:
            nombre_tranches = self._session.scalar(
                select(func.count())
                .select_from(TrancheTable)
                .where(TrancheTable.simulation_id == row.simulation_id)
            )
            summaries.append(
                SimulationResume(
                    simulation_id=row.simulation_id,
                    nom=row.nom,
                    cree_le=row.cree_le,
                    horizon_jours=row.horizon_jours,
                    nombre_tranches=int(nombre_tranches or 0),
                )
            )
        return summaries

    def create(
        self,
        payload: SimulationCreation,
        simulation_id: UUID | None = None,
    ) -> Simulation:
        """Crée une simulation complète et la renvoie."""
        simulation = Simulation(
            simulation_id=simulation_id or uuid4(),
            nom=payload.nom,
            cree_le=datetime.now(UTC),
            horizon_jours=payload.horizon_jours,
            prix_spot_eur_mwh=list(payload.prix_spot_eur_mwh),
            demande_nationale_mwh=list(payload.demande_nationale_mwh),
            valeur_usage_eur_mwh=list(payload.valeur_usage_eur_mwh),
            tranches=list(payload.tranches),
        )
        return self._persist(simulation)

    def get(
        self,
        simulation_id: UUID,
    ) -> Simulation | None:
        """Charge et reconstruit une simulation complète, ou ``None``."""
        row = self._session.get(SimulationTable, simulation_id)
        if row is None:
            return None

        daily_rows = list(
            self._session.exec(
                select(DonneeJournaliereTable)
                .where(DonneeJournaliereTable.simulation_id == simulation_id)
                .order_by("jour")
            ).all()
        )
        tranche_rows = list(
            self._session.exec(
                select(TrancheTable)
                .where(TrancheTable.simulation_id == simulation_id)
                .order_by("identifiant")
            ).all()
        )
        arret_rows = list(
            self._session.exec(
                select(ArretTable)
                .where(ArretTable.simulation_id == simulation_id)
                .order_by("jour_debut", "id")
            ).all()
        )
        modulation_rows = list(
            self._session.exec(
                select(ModulationTable)
                .where(ModulationTable.simulation_id == simulation_id)
                .order_by("jour_debut", "id")
            ).all()
        )

        jours = [daily_row.jour for daily_row in daily_rows]
        expected = list(range(row.horizon_jours))
        if jours != expected:
            raise ValueError(
                "donnees_journalieres rows must be exactly 0.."
                f"{row.horizon_jours - 1} for simulation {row.simulation_id}: "
                f"got {jours}"
            )

        arrets: dict[str, list[Arret]] = defaultdict(list)
        for arret_row in arret_rows:
            arrets[arret_row.tranche_id].append(
                Arret(
                    type_arret=arret_row.type_arret,
                    jour_debut=arret_row.jour_debut,
                    jour_fin=arret_row.jour_fin,
                )
            )

        modulations: dict[str, list[Modulation]] = defaultdict(list)
        for modulation_row in modulation_rows:
            modulations[modulation_row.tranche_id].append(
                Modulation(
                    jour_debut=modulation_row.jour_debut,
                    jour_fin=modulation_row.jour_fin,
                    facteur=modulation_row.facteur,
                )
            )

        return Simulation(
            simulation_id=row.simulation_id,
            nom=row.nom,
            cree_le=row.cree_le,
            horizon_jours=row.horizon_jours,
            prix_spot_eur_mwh=[daily_row.prix_spot_eur_mwh for daily_row in daily_rows],
            demande_nationale_mwh=[
                daily_row.demande_nationale_mwh for daily_row in daily_rows
            ],
            valeur_usage_eur_mwh=[
                daily_row.valeur_usage_eur_mwh for daily_row in daily_rows
            ],
            tranches=[
                SimulationTranche(
                    tranche=Tranche(
                        identifiant=tranche_row.identifiant,
                        code_eic=tranche_row.code_eic,
                        puissance_nominale_mw=tranche_row.puissance_nominale_mw,
                        jepp_initial=tranche_row.jepp_initial,
                    ),
                    arrets=arrets.get(tranche_row.identifiant, []),
                    modulations=modulations.get(tranche_row.identifiant, []),
                )
                for tranche_row in tranche_rows
            ],
        )

    def update(
        self,
        simulation_id: UUID,
        payload: ParametresSimulation,
    ) -> Simulation | None:
        """Remplace le nom, l'horizon et les séries nationales."""
        simulation = self.get(simulation_id)
        if simulation is None:
            return None

        updated = Simulation(
            simulation_id=simulation.simulation_id,
            nom=payload.nom,
            cree_le=simulation.cree_le,
            horizon_jours=payload.horizon_jours,
            prix_spot_eur_mwh=list(payload.prix_spot_eur_mwh),
            demande_nationale_mwh=list(payload.demande_nationale_mwh),
            valeur_usage_eur_mwh=list(payload.valeur_usage_eur_mwh),
            tranches=list(simulation.tranches),
        )
        return self._replace(updated)

    def update_tranche(
        self,
        simulation_id: UUID,
        plant_id: str,
        payload: ConfigurationTranche,
    ) -> Simulation | None:
        """Remplace la configuration d'une tranche sans changer son identifiant."""
        simulation = self.get(simulation_id)
        if simulation is None:
            return None
        if plant_id not in {entry.tranche.identifiant for entry in simulation.tranches}:
            return None

        tranches = [
            SimulationTranche(
                tranche=Tranche(
                    identifiant=entry.tranche.identifiant,
                    code_eic=payload.code_eic,
                    puissance_nominale_mw=payload.puissance_nominale_mw,
                    jepp_initial=payload.jepp_initial,
                ),
                arrets=list(entry.arrets),
                modulations=list(entry.modulations),
            )
            if entry.tranche.identifiant == plant_id
            else SimulationTranche(
                tranche=entry.tranche,
                arrets=list(entry.arrets),
                modulations=list(entry.modulations),
            )
            for entry in simulation.tranches
        ]

        updated = Simulation(
            simulation_id=simulation.simulation_id,
            nom=simulation.nom,
            cree_le=simulation.cree_le,
            horizon_jours=simulation.horizon_jours,
            prix_spot_eur_mwh=list(simulation.prix_spot_eur_mwh),
            demande_nationale_mwh=list(simulation.demande_nationale_mwh),
            valeur_usage_eur_mwh=list(simulation.valeur_usage_eur_mwh),
            tranches=tranches,
        )
        return self._replace(updated)

    def add_tranche(
        self,
        simulation_id: UUID,
        payload: SimulationTranche,
    ) -> Simulation | None:
        """Ajoute une tranche à une simulation existante."""
        simulation = self.get(simulation_id)
        if simulation is None:
            return None

        updated = Simulation(
            simulation_id=simulation.simulation_id,
            nom=simulation.nom,
            cree_le=simulation.cree_le,
            horizon_jours=simulation.horizon_jours,
            prix_spot_eur_mwh=list(simulation.prix_spot_eur_mwh),
            demande_nationale_mwh=list(simulation.demande_nationale_mwh),
            valeur_usage_eur_mwh=list(simulation.valeur_usage_eur_mwh),
            tranches=[*simulation.tranches, payload],
        )
        return self._replace(updated)

    def replace_arrets(
        self,
        simulation_id: UUID,
        plant_id: str,
        arrets: list[Arret],
    ) -> Simulation | None:
        """Remplace les arrêts d'une tranche, puis persiste la simulation."""
        simulation = self.get(simulation_id)
        if simulation is None:
            return None
        updated = self._with_schedule(simulation, plant_id, arrets, None)
        if updated is None:
            return None
        return self._replace(updated)

    def replace_modulations(
        self,
        simulation_id: UUID,
        plant_id: str,
        modulations: list[Modulation],
    ) -> Simulation | None:
        """Remplace les modulations d'une tranche, puis persiste la simulation."""
        simulation = self.get(simulation_id)
        if simulation is None:
            return None
        updated = self._with_schedule(simulation, plant_id, None, modulations)
        if updated is None:
            return None
        return self._replace(updated)

    def delete(self, simulation_id: UUID) -> bool:
        """Supprime une simulation et ses dépendances."""
        row = self._session.get(SimulationTable, simulation_id)
        if row is None:
            return False
        self._session.delete(row)
        self._session.commit()
        return True
