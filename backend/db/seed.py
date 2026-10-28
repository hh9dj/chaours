from uuid import UUID

import numpy as np

from api.context import AppContext
from api.schemas import SimulationCreation
from core.models import Arret, Modulation, SimulationTranche, Tranche, TypeArret
from db.repository import SimulationRepository

DEMO_SIMULATION_ID = UUID("2f9e3c1a-8b7d-4e6f-9a2b-3c4d5e6f7a8b")
DEMO_SIMULATION_NAME = "Démo"


def _arrondir(valeurs: np.ndarray) -> list[float]:
    return [round(float(valeur), 2) for valeur in valeurs]


def build_demo_simulation() -> SimulationCreation:
    """Construit un scénario de démonstration riche et reproductible.

    Le scénario produit les quatre familles d'alertes :

    - ``NEUTRONIC_ANOMALY`` sur P4 avant son arrêt ;
    - ``REMIT_UMM`` aux frontières des arrêts et des modulations ;
    - ``RTE_DEFICIT`` pendant les arrêts hivernaux simultanés ;
    - ``SPOT_BELOW_USAGE_VALUE`` quand le prix spot saisonnier passe sous la
      valeur d'usage.

    Les séries sont déterministes pour que la démonstration soit stable.
    """
    horizon = 365
    jours = np.arange(horizon, dtype=np.float64)
    saison = np.cos(2.0 * np.pi * (jours - 15.0) / horizon)
    generateur = np.random.default_rng(20261027)

    prix_spot = 72.0 + 20.0 * saison + generateur.normal(0.0, 6.0, horizon)
    demande = 68_000.0 + 12_000.0 * saison + generateur.normal(0.0, 900.0, horizon)
    demande = np.maximum(demande, 45_000.0)
    valeur_usage = np.full(horizon, 75.0)

    tranches = [
        SimulationTranche(
            tranche=Tranche(
                identifiant="P1",
                code_eic="DEMO-P1",
                puissance_nominale_mw=900.0,
                jepp_initial=320.0,
            ),
            arrets=[
                Arret(type_arret=TypeArret.ASR, jour_debut=30, jour_fin=45),
                Arret(type_arret=TypeArret.VP, jour_debut=200, jour_fin=230),
            ],
            modulations=[
                Modulation(jour_debut=90, jour_fin=105, facteur=0.5),
            ],
        ),
        SimulationTranche(
            tranche=Tranche(
                identifiant="P2",
                code_eic="DEMO-P2",
                puissance_nominale_mw=1_300.0,
                jepp_initial=400.0,
            ),
            arrets=[
                Arret(type_arret=TypeArret.VD, jour_debut=15, jour_fin=60),
            ],
            modulations=[
                Modulation(jour_debut=70, jour_fin=85, facteur=0.4),
            ],
        ),
        SimulationTranche(
            tranche=Tranche(
                identifiant="P3",
                code_eic="DEMO-P3",
                puissance_nominale_mw=900.0,
                jepp_initial=300.0,
            ),
            arrets=[
                Arret(type_arret=TypeArret.ASR, jour_debut=40, jour_fin=70),
                Arret(type_arret=TypeArret.VP, jour_debut=300, jour_fin=320),
            ],
            modulations=[
                Modulation(jour_debut=120, jour_fin=140, facteur=0.35),
            ],
        ),
        SimulationTranche(
            tranche=Tranche(
                identifiant="P4",
                code_eic="DEMO-P4",
                puissance_nominale_mw=1_450.0,
                jepp_initial=150.0,
            ),
            arrets=[
                Arret(type_arret=TypeArret.ASR, jour_debut=220, jour_fin=250),
            ],
            modulations=[
                Modulation(jour_debut=100, jour_fin=115, facteur=0.6),
            ],
        ),
    ]

    return SimulationCreation(
        nom=DEMO_SIMULATION_NAME,
        horizon_jours=horizon,
        prix_spot_eur_mwh=_arrondir(prix_spot),
        demande_nationale_mwh=_arrondir(demande),
        valeur_usage_eur_mwh=_arrondir(valeur_usage),
        tranches=tranches,
    )


def ensure_demo_simulation(context: AppContext) -> bool:
    """Ajoute la démonstration par défaut si elle n'existe pas déjà."""
    with context.session_factory() as session:
        repository = SimulationRepository(session)
        if repository.get(DEMO_SIMULATION_ID) is not None:
            return False
        repository.create(
            build_demo_simulation(),
            simulation_id=DEMO_SIMULATION_ID,
        )
        return True
