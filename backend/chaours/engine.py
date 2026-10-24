from __future__ import annotations

from chaours.types import Scenario, SimulationResult


class NucliEngine:
    """Orchestre le pipeline de calcul de la phase 1.

    Ordre du pipeline :

    1. facteurs de charge nominaux
    2. fenêtres de modulation manuelle
    3. masque de maintenance, appliqué en dernier pour que les arrêts
       gagnent toujours
    4. épuisement JEPP et stretch-out
    5. énergie journalière, agrégation nationale et déficits
    6. alertes neutroniques, REMIT, déficits et prix spot sous la valeur
       d'usage

    Le moteur est sans état : chaque exécution reçoit un ``Scenario`` complet.
    """

    def run(self, scenario: Scenario) -> SimulationResult:
        """Exécute une simulation et renvoie les trajectoires et les alertes."""
        raise NotImplementedError
