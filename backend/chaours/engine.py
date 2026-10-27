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
    Alerte,
    ResultatSimulation,
    ResultatTranche,
    Simulation,
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

    Le moteur est sans état : chaque exécution reçoit un ``Simulation`` complet
    déjà validé par Pydantic.
    """

    def run(self, simulation: Simulation) -> ResultatSimulation:
        """Exécute une simulation et renvoie les trajectoires et alertes."""
        start = time.perf_counter()

        prix_spot = np.asarray(
            simulation.prix_spot_eur_mwh,
            dtype=np.float64,
        )
        valeur_usage = np.asarray(
            simulation.valeur_usage_eur_mwh,
            dtype=np.float64,
        )
        demande = np.asarray(
            simulation.demande_nationale_mwh,
            dtype=np.float64,
        )
        horizon = simulation.horizon_jours
        entries = simulation.tranches
        tranche_count = len(entries)
        tranche_ids = tuple(
            entry.tranche.identifiant for entry in entries
        )

        nominal_factors = np.ones(
            (tranche_count, horizon),
            dtype=np.float64,
        )
        requested_factors = np.empty_like(nominal_factors)

        for index, entry in enumerate(entries):
            modulated = apply_manual_modulation(
                nominal_factors[index],
                entry.modulations,
            )
            mask = maintenance_mask(entry.arrets, horizon)
            requested_factors[index] = apply_maintenance(
                modulated,
                mask,
            )

        actual_factors = np.zeros_like(requested_factors)
        remaining_jepp = np.zeros_like(requested_factors)
        depletion_by_tranche: list[tuple[int, ...]] = []

        for index, entry in enumerate(entries):
            actual, remaining, depletion_days = simulate_stock_cycles(
                requested_factors[index],
                entry.tranche.jepp_initial,
                entry.arrets,
            )
            actual_factors[index] = actual
            remaining_jepp[index] = remaining
            depletion_by_tranche.append(depletion_days)

        nominal_power_mw = np.array(
            [
                entry.tranche.puissance_nominale_mw
                for entry in entries
            ],
            dtype=np.float64,
        )
        energy_by_tranche = energy_mwh(actual_factors, nominal_power_mw)
        supply_mwh = national_supply(energy_by_tranche)
        deficit_day_indices = deficit_days(supply_mwh, demande)
        variation_mw = daily_power_variation_mw(energy_by_tranche)

        tranche_results = [
            ResultatTranche(
                tranche_id=entry.tranche.identifiant,
                facteurs_production=actual_factors[index].tolist(),
                energie_mwh=energy_by_tranche[index].tolist(),
                jepp_restant=remaining_jepp[index].tolist(),
                jours_epuisement=list(depletion_by_tranche[index]),
            )
            for index, entry in enumerate(entries)
        ]

        alerts: list[Alerte] = []
        alerts.extend(
            neutronic_alerts(
                tranche_results,
                simulation.arrets_par_tranche,
            )
        )
        alerts.extend(remit_alerts(variation_mw, tranche_ids))
        alerts.extend(deficit_alerts(deficit_day_indices))
        alerts.extend(
            spot_below_usage_value_alerts(prix_spot, valeur_usage)
        )

        execution_time_ms = (time.perf_counter() - start) * 1000.0

        return ResultatSimulation(
            simulation_id=simulation.simulation_id,
            duree_execution_ms=execution_time_ms,
            tranches=tranche_results,
            offre_nationale_mwh=supply_mwh.tolist(),
            demande_mwh=demande.tolist(),
            jours_deficit=deficit_day_indices.tolist(),
            alertes=alerts,
        )
