from __future__ import annotations

import argparse
import statistics
import time
from collections import Counter
from collections.abc import Sequence

import numpy as np

from chaours.constants import DEFAULT_HORIZON_DAYS
from chaours.engine import NucliEngine
from chaours.types import (
    AlertKind,
    Maintenance,
    Modulation,
    OutageKind,
    Plant,
    Scenario,
    Simulation,
)


def mock_scenario() -> Scenario:
    """Construit un scénario de démonstration avec plusieurs tranches."""
    horizon = DEFAULT_HORIZON_DAYS
    usage_values = {"P1": 60.0, "P2": 85.0, "P3": 70.0}

    plants = [
        Simulation(
            plant=Plant(
                id="P1",
                eic_code="MOCK-P1",
                nominal_power_mw=900.0,
                initial_jepp=300.0,
            ),
            maintenances=[
                Maintenance(kind=OutageKind.ASR, start_day=30, end_day=45),
                Maintenance(kind=OutageKind.VP, start_day=200, end_day=230),
            ],
        ),
        Simulation(
            plant=Plant(
                id="P2",
                eic_code="MOCK-P2",
                nominal_power_mw=1_300.0,
                initial_jepp=280.0,
            ),
            maintenances=[
                Maintenance(kind=OutageKind.VD, start_day=120, end_day=170),
            ],
            modulations=[
                Modulation(start_day=10, end_day=20, factor=0.6),
            ],
        ),
        Simulation(
            plant=Plant(
                id="P3",
                eic_code="MOCK-P3",
                nominal_power_mw=900.0,
                initial_jepp=260.0,
            ),
            maintenances=[
                Maintenance(kind=OutageKind.ASR, start_day=80, end_day=95),
            ],
            modulations=[
                Modulation(start_day=150, end_day=180, factor=0.35),
            ],
        ),
    ]

    return Scenario(
        name="mock",
        horizon_days=horizon,
        spot_prices=[80.0] * horizon,
        demand_mwh=[52_000.0] * horizon,
        usage_values_eur_mwh=usage_values,
        plants=plants,
    )


def benchmark_scenario() -> Scenario:
    """Construit un scénario reproductible de 56 tranches sur 365 jours."""
    horizon = 365
    rng = np.random.default_rng(20261025)

    usage_values: dict[str, float] = {}
    plants: list[Simulation] = []

    for index in range(1, 57):
        plant_id = f"B{index:02d}"
        start = 15 + (index * 6) % 320
        length = 12 + (index % 4) * 5
        maintenance_kind = (
            OutageKind.ASR,
            OutageKind.VP,
            OutageKind.VD,
        )[index % 3]

        modulations: list[Modulation] = []
        if index % 5 == 0:
            modulation_start = 5 + (index * 3) % 340
            modulations.append(
                Modulation(
                    start_day=modulation_start,
                    end_day=modulation_start + 10,
                    factor=float(0.3 + (index % 4) * 0.15),
                )
            )

        plants.append(
            Simulation(
                plant=Plant(
                    id=plant_id,
                    eic_code=f"BENCH-{index:02d}",
                    nominal_power_mw=float(rng.integers(900, 1_500)),
                    initial_jepp=float(rng.integers(240, 320)),
                ),
                maintenances=[
                    Maintenance(
                        kind=maintenance_kind,
                        start_day=start,
                        end_day=start + length,
                    ),
                ],
                modulations=modulations,
            )
        )
        usage_values[plant_id] = float(55.0 + (index % 5) * 5.0)

    return Scenario(
        name="benchmark-56x365",
        horizon_days=horizon,
        spot_prices=rng.normal(80.0, 20.0, horizon).tolist(),
        demand_mwh=[58_000.0] * horizon,
        usage_values_eur_mwh=usage_values,
        plants=plants,
    )


def _print_scenario_result(scenario: Scenario) -> None:
    result = NucliEngine().run(scenario)
    alert_counts = Counter(alert.kind for alert in result.alerts)

    print(f"scenario={result.scenario_id} horizon={scenario.horizon_days}d")
    print(f"plants={len(result.plants)}")
    print(f"deficit_days={len(result.deficit_days)}")
    for kind in AlertKind:
        print(f"alerts[{kind.value}]={alert_counts.get(kind, 0)}")
    print(f"alerts_total={len(result.alerts)}")
    print(f"execution_time_ms={result.execution_time_ms:.3f}")


def _run_benchmark() -> None:
    scenario = benchmark_scenario()
    engine = NucliEngine()
    durations: list[float] = []

    for _ in range(20):
        started = time.perf_counter()
        engine.run(scenario)
        durations.append((time.perf_counter() - started) * 1000.0)

    minimum = min(durations)
    median = statistics.median(durations)
    maximum = max(durations)

    print(f"scenario={scenario.name} horizon={scenario.horizon_days}d")
    print(f"plants={len(scenario.plants)}")
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

    _print_scenario_result(mock_scenario())


if __name__ == "__main__":
    main()
