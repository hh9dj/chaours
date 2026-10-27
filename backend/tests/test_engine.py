import numpy as np

from chaours.engine import NucliEngine
from chaours.types import (
    Arret,
    Modulation,
    Simulation,
    SimulationTranche,
    Tranche,
    TypeAlerte,
    TypeArret,
)


def _tranche(
    identifiant: str = "P1",
    puissance_nominale_mw: float = 1_000.0,
    jepp_initial: float = 100.0,
) -> Tranche:
    return Tranche(
        identifiant=identifiant,
        code_eic=f"EIC-{identifiant}",
        puissance_nominale_mw=puissance_nominale_mw,
        jepp_initial=jepp_initial,
    )


def _entry(
    tranche: Tranche | None = None,
    arrets: tuple[Arret, ...] = (),
    modulations: tuple[Modulation, ...] = (),
) -> SimulationTranche:
    return SimulationTranche(
        tranche=tranche if tranche is not None else _tranche(),
        arrets=list(arrets),
        modulations=list(modulations),
    )


def _simulation(
    horizon_jours: int = 4,
    prix_spot_eur_mwh: list[float] | None = None,
    demande_nationale_mwh: list[float] | None = None,
    valeur_usage_eur_mwh: list[float] | None = None,
    tranches: list[SimulationTranche] | None = None,
) -> Simulation:
    return Simulation(
        nom="test",
        horizon_jours=horizon_jours,
        prix_spot_eur_mwh=(
            prix_spot_eur_mwh
            if prix_spot_eur_mwh is not None
            else [80.0] * horizon_jours
        ),
        demande_nationale_mwh=(
            demande_nationale_mwh
            if demande_nationale_mwh is not None
            else [0.0] * horizon_jours
        ),
        valeur_usage_eur_mwh=(
            valeur_usage_eur_mwh
            if valeur_usage_eur_mwh is not None
            else [60.0] * horizon_jours
        ),
        tranches=tranches if tranches is not None else [_entry()],
    )


def _arret(jour_debut: int, jour_fin: int) -> Arret:
    return Arret(
        type_arret=TypeArret.ASR,
        jour_debut=jour_debut,
        jour_fin=jour_fin,
    )


def test_engine_runs_full_pipeline_in_order():
    simulation = _simulation(
        horizon_jours=5,
        prix_spot_eur_mwh=[80.0] * 5,
        demande_nationale_mwh=[0.0] * 5,
        tranches=[
            _entry(
                _tranche(jepp_initial=100.0),
                arrets=(_arret(2, 3),),
                modulations=(
                    Modulation(jour_debut=1, jour_fin=4, facteur=0.5),
                ),
            )
        ],
    )

    result = NucliEngine().run(simulation)

    np.testing.assert_allclose(
        result.tranches[0].facteurs_production,
        [1.0, 0.5, 0.0, 0.5, 1.0],
    )


def test_engine_returns_one_result_per_tranche():
    simulation = _simulation(
        horizon_jours=3,
        prix_spot_eur_mwh=[80.0] * 3,
        demande_nationale_mwh=[0.0] * 3,
        tranches=[
            _entry(_tranche("P1")),
            _entry(_tranche("P2", 500.0)),
        ],
    )

    result = NucliEngine().run(simulation)

    assert [tranche.tranche_id for tranche in result.tranches] == [
        "P1",
        "P2",
    ]


def test_engine_returns_national_supply_and_deficits():
    simulation = _simulation(
        horizon_jours=3,
        prix_spot_eur_mwh=[80.0] * 3,
        demande_nationale_mwh=[5_000.0, 4_800.0, 4_000.0],
        tranches=[
            _entry(_tranche("P1", 100.0)),
            _entry(_tranche("P2", 100.0)),
        ],
    )

    result = NucliEngine().run(simulation)

    np.testing.assert_allclose(
        result.offre_nationale_mwh,
        [4_800.0] * 3,
    )
    np.testing.assert_array_equal(result.jours_deficit, [0])
    np.testing.assert_allclose(
        result.demande_mwh,
        [5_000.0, 4_800.0, 4_000.0],
    )


def test_engine_recharge_resets_stock_and_restores_production():
    simulation = _simulation(
        horizon_jours=6,
        prix_spot_eur_mwh=[80.0] * 6,
        demande_nationale_mwh=[0.0] * 6,
        tranches=[
            _entry(
                _tranche(jepp_initial=1.0),
                arrets=(_arret(2, 3),),
            )
        ],
    )

    result = NucliEngine().run(simulation)

    tranche_result = result.tranches[0]
    np.testing.assert_allclose(
        tranche_result.facteurs_production,
        [1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    )
    assert tranche_result.facteurs_production[3] == 1.0
    assert tranche_result.jours_epuisement == [1, 4]


def test_engine_depletion_clips_energy_and_supply():
    simulation = _simulation(
        horizon_jours=2,
        prix_spot_eur_mwh=[80.0] * 2,
        demande_nationale_mwh=[0.0] * 2,
        tranches=[
            _entry(
                _tranche(
                    puissance_nominale_mw=100.0,
                    jepp_initial=0.5,
                )
            ),
        ],
    )

    result = NucliEngine().run(simulation)

    tranche_result = result.tranches[0]
    np.testing.assert_allclose(
        tranche_result.facteurs_production,
        [0.5, 0.0],
    )
    np.testing.assert_allclose(
        tranche_result.energie_mwh,
        [1_200.0, 0.0],
    )
    np.testing.assert_allclose(
        result.offre_nationale_mwh,
        [1_200.0, 0.0],
    )
    assert tranche_result.jours_epuisement == [0]


def test_engine_alert_assembly_has_deterministic_order():
    simulation = _simulation(
        horizon_jours=4,
        prix_spot_eur_mwh=[10.0, 100.0, 100.0, 100.0],
        demande_nationale_mwh=[0.0, 30_000.0, 0.0, 0.0],
        tranches=[_entry(_tranche(jepp_initial=1.0))],
    )

    result = NucliEngine().run(simulation)

    assert [alerte.type_alerte for alerte in result.alertes] == [
        TypeAlerte.NEUTRONIC_ANOMALY,
        TypeAlerte.REMIT_UMM,
        TypeAlerte.RTE_DEFICIT,
        TypeAlerte.SPOT_BELOW_USAGE_VALUE,
    ]
    assert result.alertes[0].jour == 1
    assert result.alertes[1].jour == 1
    assert result.alertes[2].jour == 1
    assert result.alertes[3].jour == 0


def test_engine_includes_national_spot_below_usage_value_alerts():
    simulation = _simulation(
        horizon_jours=2,
        prix_spot_eur_mwh=[10.0, 50.0],
        demande_nationale_mwh=[0.0, 0.0],
        valeur_usage_eur_mwh=[60.0, 60.0],
        tranches=[_entry(_tranche(jepp_initial=100.0))],
    )

    result = NucliEngine().run(simulation)

    spot_alerts = [
        alerte
        for alerte in result.alertes
        if alerte.type_alerte == TypeAlerte.SPOT_BELOW_USAGE_VALUE
    ]
    assert [alerte.jour for alerte in spot_alerts] == [0, 1]
    assert all(alerte.tranche_id is None for alerte in spot_alerts)


def test_engine_execution_time_is_non_negative():
    result = NucliEngine().run(_simulation())

    assert result.duree_execution_ms >= 0.0


def test_engine_runs_without_tranches():
    simulation = _simulation(
        horizon_jours=3,
        prix_spot_eur_mwh=[80.0] * 3,
        demande_nationale_mwh=[1_000.0] * 3,
        tranches=[],
    )

    result = NucliEngine().run(simulation)

    assert result.tranches == []
    assert result.offre_nationale_mwh == [0.0, 0.0, 0.0]
    assert result.jours_deficit == [0, 1, 2]
