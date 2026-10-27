import argparse
from collections import Counter
from collections.abc import Sequence

from core.engine.pipeline import SimulationEngine
from core.models import (
    DEFAULT_HORIZON_DAYS,
    Arret,
    Modulation,
    Simulation,
    SimulationTranche,
    Tranche,
    TypeAlerte,
    TypeArret,
)


def mock_simulation() -> Simulation:
    """Construit un scénario de démonstration avec plusieurs tranches."""
    horizon = DEFAULT_HORIZON_DAYS

    tranches = [
        SimulationTranche(
            tranche=Tranche(
                identifiant="P1",
                code_eic="MOCK-P1",
                puissance_nominale_mw=900.0,
                jepp_initial=300.0,
            ),
            arrets=[
                Arret(type_arret=TypeArret.ASR, jour_debut=30, jour_fin=45),
                Arret(type_arret=TypeArret.VP, jour_debut=200, jour_fin=230),
            ],
        ),
        SimulationTranche(
            tranche=Tranche(
                identifiant="P2",
                code_eic="MOCK-P2",
                puissance_nominale_mw=1_300.0,
                jepp_initial=280.0,
            ),
            arrets=[
                Arret(
                    type_arret=TypeArret.VD,
                    jour_debut=120,
                    jour_fin=170,
                ),
            ],
            modulations=[
                Modulation(jour_debut=10, jour_fin=20, facteur=0.6),
            ],
        ),
        SimulationTranche(
            tranche=Tranche(
                identifiant="P3",
                code_eic="MOCK-P3",
                puissance_nominale_mw=900.0,
                jepp_initial=260.0,
            ),
            arrets=[
                Arret(type_arret=TypeArret.ASR, jour_debut=80, jour_fin=95),
            ],
            modulations=[
                Modulation(jour_debut=150, jour_fin=180, facteur=0.35),
            ],
        ),
    ]

    return Simulation(
        nom="mock",
        horizon_jours=horizon,
        prix_spot_eur_mwh=[80.0] * horizon,
        demande_nationale_mwh=[52_000.0] * horizon,
        valeur_usage_eur_mwh=[70.0] * horizon,
        tranches=tranches,
    )


def _print_simulation_result(simulation: Simulation) -> None:
    result = SimulationEngine().run(simulation)
    alert_counts = Counter(alerte.type_alerte for alerte in result.alertes)

    print(f"simulation={result.simulation_id} horizon={simulation.horizon_jours}d")
    print(f"tranches={len(result.tranches)}")
    print(f"jours_deficit={len(result.jours_deficit)}")
    for type_alerte in TypeAlerte:
        print(f"alertes[{type_alerte.value}]={alert_counts.get(type_alerte, 0)}")
    print(f"alertes_total={len(result.alertes)}")
    print(f"execution_time_ms={result.duree_execution_ms:.3f}")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python cli.py",
        description="Simulateur de planification des arrêts nucléaires.",
    )
    parser.parse_args(argv)

    _print_simulation_result(mock_simulation())


if __name__ == "__main__":
    main()
