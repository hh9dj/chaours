from __future__ import annotations

from .types import Scenario, SimulationResult


class NucliEngine:
    """Orchestre le pipeline de calcul de la phase 1.

    Ordre du pipeline :

    1. facteurs de charge nominaux
    2. arbitrage économique à partir du prix spot et des valeurs d'usage
    3. fenêtres de modulation manuelle
    4. masque de maintenance, appliqué en dernier pour que les arrêts
       gagnent toujours
    5. épuisement JEPP et stretch-out
    6. énergie journalière, agrégation nationale et déficits
    7. alertes neutroniques, REMIT et déficits

    Le moteur est sans état : chaque exécution reçoit un ``Scenario`` complet.
    """

    def run(self, scenario: Scenario) -> SimulationResult:
        """Exécute une simulation et renvoie les trajectoires et les alertes."""
        raise NotImplementedError
