from __future__ import annotations

import time

import numpy as np

from chaours.aggregation import (
    daily_power_variation_mw,
    deficit_days,
    energy_mwh,
    national_supply,
)
from chaours.alerts import (
    deficit_alerts,
    neutronic_alerts,
    remit_alerts,
    spot_below_usage_value_alerts,
)
from chaours.jepp import simulate_stock_cycles
from chaours.production import (
    apply_maintenance,
    apply_manual_modulation,
    maintenance_mask,
)
from chaours.types import (
    Alert,
    PlantResult,
    Scenario,
    SimulationResult,
)


class NucliEngine:
    """Orchestre le pipeline de calcul de la phase 1.

    Ordre du pipeline, appliqué tranche par tranche pour la production :

    1. facteurs de charge nominaux
    2. fenêtres de modulation manuelle
    3. masque de maintenance, appliqué en dernier pour que les arrêts
       gagnent toujours
    4. déplétion JEPP, rechargements aux arrêts et limite physique dure du
       stock, sans dégradation automatique
    5. énergie journalière, agrégation nationale et déficits
    6. alertes neutroniques, REMIT, déficits et prix spot sous la valeur
       d'usage

    Le moteur est sans état : chaque exécution reçoit un ``Scenario`` complet
    déjà validé par Pydantic.
    """

    def run(self, scenario: Scenario) -> SimulationResult:
        """Exécute une simulation et renvoie les trajectoires et les alertes."""
        start = time.perf_counter()

        spot_prices = np.asarray(scenario.spot_prices, dtype=np.float64)
        demand_mwh = np.asarray(scenario.demand_mwh, dtype=np.float64)
        horizon = scenario.horizon_days
        entries = scenario.plants
        plant_count = len(entries)
        plant_ids = tuple(entry.plant.id for entry in entries)

        nominal_factors = np.ones((plant_count, horizon), dtype=np.float64)
        requested_factors = np.empty_like(nominal_factors)

        for plant_index, entry in enumerate(entries):
            modulated = apply_manual_modulation(
                nominal_factors[plant_index],
                entry.modulations,
            )
            mask = maintenance_mask(entry.maintenances, horizon)
            requested_factors[plant_index] = apply_maintenance(
                modulated,
                mask,
            )

        actual_factors = np.zeros_like(requested_factors)
        remaining_jepp = np.zeros_like(requested_factors)
        depletion_by_plant: list[tuple[int, ...]] = []

        for plant_index, entry in enumerate(entries):
            actual, remaining, depletion_days = simulate_stock_cycles(
                requested_factors[plant_index],
                entry.plant.initial_jepp,
                entry.maintenances,
            )
            actual_factors[plant_index] = actual
            remaining_jepp[plant_index] = remaining
            depletion_by_plant.append(depletion_days)

        nominal_power_mw = np.array(
            [entry.plant.nominal_power_mw for entry in entries],
            dtype=np.float64,
        )
        energy_by_plant = energy_mwh(actual_factors, nominal_power_mw)
        supply_mwh = national_supply(energy_by_plant)
        deficit_day_indices = deficit_days(supply_mwh, demand_mwh)
        variation_mw = daily_power_variation_mw(energy_by_plant)

        plant_results = [
            PlantResult(
                plant_id=entry.plant.id,
                production_factors=actual_factors[plant_index].tolist(),
                energy_mwh=energy_by_plant[plant_index].tolist(),
                remaining_jepp=remaining_jepp[plant_index].tolist(),
                depletion_days=list(depletion_by_plant[plant_index]),
            )
            for plant_index, entry in enumerate(entries)
        ]

        alerts: list[Alert] = []
        alerts.extend(
            neutronic_alerts(
                plant_results,
                scenario.maintenances_by_plant,
            )
        )
        alerts.extend(remit_alerts(variation_mw, plant_ids))
        alerts.extend(deficit_alerts(deficit_day_indices))
        alerts.extend(
            spot_below_usage_value_alerts(
                spot_prices,
                tuple(entry.plant for entry in entries),
                scenario.usage_values_eur_mwh,
            )
        )

        execution_time_ms = (time.perf_counter() - start) * 1000.0

        return SimulationResult(
            scenario_id=scenario.scenario_id,
            execution_time_ms=execution_time_ms,
            plants=plant_results,
            national_supply_mwh=supply_mwh.tolist(),
            demand_mwh=demand_mwh.tolist(),
            deficit_days=deficit_day_indices.tolist(),
            alerts=alerts,
        )
