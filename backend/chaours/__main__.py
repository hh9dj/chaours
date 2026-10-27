import argparse
import statistics
import time
from collections import Counter
from collections.abc import Sequence

import numpy as np

from chaours.constants import DEFAULT_HORIZON_DAYS
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


def benchmark_simulation() -> Simulation:
    """Construit un scénario reproductible de 56 tranches sur 365 jours."""
    horizon = 365
    rng = np.random.default_rng(20261025)

    tranches: list[SimulationTranche] = []

    for index in range(1, 57):
        identifiant = f"B{index:02d}"
        start = 15 + (index * 6) % 320
        length = 12 + (index % 4) * 5
        type_arret = (
            TypeArret.ASR,
            TypeArret.VP,
            TypeArret.VD,
        )[index % 3]

        modulations: list[Modulation] = []
        if index % 5 == 0:
            modulation_start = 5 + (index * 3) % 340
            modulations.append(
                Modulation(
                    jour_debut=modulation_start,
                    jour_fin=modulation_start + 10,
                    facteur=float(0.3 + (index % 4) * 0.15),
                )
            )

        tranches.append(
            SimulationTranche(
                tranche=Tranche(
                    identifiant=identifiant,
                    code_eic=f"BENCH-{index:02d}",
                    puissance_nominale_mw=float(
                        rng.integers(900, 1_500)
                    ),
                    jepp_initial=float(rng.integers(240, 320)),
                ),
                arrets=[
                    Arret(
                        type_arret=type_arret,
                        jour_debut=start,
                        jour_fin=start + length,
                    ),
                ],
                modulations=modulations,
            )
        )

    return Simulation(
        nom="benchmark-56x365",
        horizon_jours=horizon,
        prix_spot_eur_mwh=rng.normal(80.0, 20.0, horizon).tolist(),
        demande_nationale_mwh=[58_000.0] * horizon,
        valeur_usage_eur_mwh=[70.0] * horizon,
        tranches=tranches,
    )


def _print_simulation_result(simulation: Simulation) -> None:
    result = NucliEngine().run(simulation)
    alert_counts = Counter(
        alerte.type_alerte for alerte in result.alertes
    )

    print(
        f"simulation={result.simulation_id} "
        f"horizon={simulation.horizon_jours}d"
    )
    print(f"tranches={len(result.tranches)}")
    print(f"jours_deficit={len(result.jours_deficit)}")
    for type_alerte in TypeAlerte:
        print(
            f"alertes[{type_alerte.value}]="
            f"{alert_counts.get(type_alerte, 0)}"
        )
    print(f"alertes_total={len(result.alertes)}")
    print(f"execution_time_ms={result.duree_execution_ms:.3f}")


def _run_benchmark() -> None:
    simulation = benchmark_simulation()
    engine = NucliEngine()
    durations: list[float] = []

    for _ in range(20):
        started = time.perf_counter()
        engine.run(simulation)
        durations.append((time.perf_counter() - started) * 1000.0)

    minimum = min(durations)
    median = statistics.median(durations)
    maximum = max(durations)

    print(f"simulation={simulation.nom} horizon={simulation.horizon_jours}d")
    print(f"tranches={len(simulation.tranches)}")
    print(f"runs={len(durations)}")
    print(f"min_ms={minimum:.3f}")
    print(f"median_ms={median:.3f}")
    print(f"max_ms={maximum:.3f}")
    print("PASS" if median < 40.0 else "FAIL")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m chaours",
        description="Simulateur de planification des arrêts nucléaires.",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Exécute le benchmark déterministe de 56 tranches sur 365 jours.",
    )
    args = parser.parse_args(argv)

    if args.benchmark:
        _run_benchmark()
        return

    _print_simulation_result(mock_simulation())


if __name__ == "__main__":
    main()
