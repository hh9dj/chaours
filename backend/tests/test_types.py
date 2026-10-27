from __future__ import annotations

from uuid import uuid4

from chaours.types import (
    Alerte,
    Arret,
    Modulation,
    ResultatSimulation,
    ResultatTranche,
    Simulation,
    SimulationTranche,
    Tranche,
    TypeAlerte,
    TypeArret,
)


def _tranche(identifiant: str = "P1") -> Tranche:
    return Tranche(
        identifiant=identifiant,
        code_eic=f"EIC-{identifiant}",
        puissance_nominale_mw=900.0,
        jepp_initial=300.0,
    )


def _entry(
    identifiant: str = "P1",
    arrets: list[Arret] | None = None,
    modulations: list[Modulation] | None = None,
) -> SimulationTranche:
    return SimulationTranche(
        tranche=_tranche(identifiant),
        arrets=list(arrets or []),
        modulations=list(modulations or []),
    )


def _simulation() -> Simulation:
    return Simulation(
        nom="test",
        horizon_jours=4,
        prix_spot_eur_mwh=[80.0] * 4,
        demande_nationale_mwh=[0.0] * 4,
        valeur_usage_eur_mwh=[60.0] * 4,
        tranches=[_entry("P1"), _entry("P2")],
    )


def test_simulation_starts_with_empty_schedule_lists():
    entry = SimulationTranche(tranche=_tranche())

    assert entry.arrets == []
    assert entry.modulations == []


def test_schedules_are_owned_by_the_simulation_entry():
    entry = _entry(
        arrets=[
            Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3)
        ],
        modulations=[Modulation(jour_debut=2, jour_fin=4, facteur=0.5)],
    )

    assert entry.arrets[0].type_arret == TypeArret.ASR
    assert entry.arrets[0].jour_debut == 1
    assert entry.arrets[0].jour_fin == 3
    assert entry.modulations[0].facteur == 0.5


def test_simulation_schedule_mappings_keep_entry_order():
    simulation = _simulation()
    simulation.tranches[0].arrets = [
        Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3)
    ]
    simulation.tranches[1].arrets = [
        Arret(type_arret=TypeArret.VP, jour_debut=2, jour_fin=4)
    ]
    simulation.tranches[0].modulations = [
        Modulation(jour_debut=1, jour_fin=2, facteur=0.5)
    ]
    simulation.tranches[1].modulations = [
        Modulation(jour_debut=2, jour_fin=3, facteur=0.7)
    ]

    assert list(simulation.arrets_par_tranche) == ["P1", "P2"]
    assert list(simulation.modulations_par_tranche) == ["P1", "P2"]
    assert simulation.arrets_par_tranche["P2"] == (
        Arret(type_arret=TypeArret.VP, jour_debut=2, jour_fin=4),
    )
    assert simulation.modulations_par_tranche["P1"] == (
        Modulation(jour_debut=1, jour_fin=2, facteur=0.5),
    )


def test_result_alerts_are_grouped_by_tranche_and_national():
    tranche_alert = Alerte(
        type_alerte=TypeAlerte.REMIT_UMM,
        jour=1,
        tranche_id="P1",
        message="Alerte tranche.",
    )
    national_alert = Alerte(
        type_alerte=TypeAlerte.RTE_DEFICIT,
        jour=2,
        tranche_id=None,
        message="Alerte nationale.",
    )
    result = ResultatSimulation(
        simulation_id=uuid4(),
        duree_execution_ms=1.0,
        tranches=[
            ResultatTranche(
                tranche_id="P1",
                facteurs_production=[1.0, 1.0, 1.0],
                energie_mwh=[1.0, 1.0, 1.0],
                jepp_restant=[1.0, 1.0, 1.0],
                jours_epuisement=[],
            )
        ],
        offre_nationale_mwh=[1.0, 1.0, 1.0],
        demande_mwh=[0.0, 0.0, 0.0],
        jours_deficit=[2],
        alertes=[tranche_alert, national_alert],
    )

    assert result.alertes_par_tranche == {"P1": (tranche_alert,)}
    assert result.alertes_nationales == (national_alert,)
