from __future__ import annotations

import numpy as np

from chaours.constants import DEFAULT_HORIZON_DAYS
from chaours.types import OutageKind, Plant, Scenario


def mock_scenario() -> Scenario:
    """Construit un scénario minimal utilisé par la CLI temporaire."""
    horizon = DEFAULT_HORIZON_DAYS
    return Scenario(
        scenario_id="mock",
        horizon_days=horizon,
        spot_prices=np.full(horizon, 80.0),
        demand_mwh=np.full(horizon, 50_000.0),
        usage_values_eur_mwh={"P1": 60.0},
        plants=(
            Plant(
                id="P1",
                eic_code="MOCK-P1",
                nominal_power_mw=900.0,
                initial_jepp=300.0,
            ),
        ),
        maintenances=(),
        modulations=(),
    )


def main() -> None:
    """CLI temporaire en attendant l'implémentation du moteur."""
    scenario = mock_scenario()
    plant = scenario.plants[0]
    print(f"scenario={scenario.scenario_id} horizon={scenario.horizon_days}d")
    print(
        f"plant={plant.id} power={plant.nominal_power_mw}MW jepp={plant.initial_jepp}"
    )
    print(f"outage kinds={[kind.value for kind in OutageKind]}")
    print("engine not implemented yet")


if __name__ == "__main__":
    main()
