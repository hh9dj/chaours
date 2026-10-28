import math
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "backend"))
sys.path.insert(0, str(RACINE / "animation"))

from core.engine.pipeline import SimulationEngine
from core.models import (
    Arret,
    Modulation,
    Simulation,
    SimulationTranche,
    Tranche,
    TypeAlerte,
    TypeArret,
)
from example_data import (
    ALERTES_NEUTRONIC,
    ALERTES_REMIT,
    ALERTES_RTE,
    ALERTES_SPOT,
    ALERTES_TOTAL,
    DEMANDE_MWH,
    ENERGIE_MWH,
    FACTEURS_REELS,
    HORIZON,
    JEPP_RESTANT,
    JOURS_DEFICIT,
    MATRICE_ALERTES,
    OFFRE_MWH,
    PRIX_SPOT_EUR_MWH,
    TRANCHES,
    VALEUR_USAGE_EUR_MWH,
)


def construire_simulation() -> Simulation:
    entrees = []
    for spec in TRANCHES:
        entrees.append(
            SimulationTranche(
                tranche=Tranche(
                    identifiant=spec.identifiant,
                    code_eic=f"DEMO-{spec.identifiant}",
                    puissance_nominale_mw=spec.puissance_mw,
                    jepp_initial=spec.jepp_initial,
                ),
                arrets=[
                    Arret(
                        type_arret=TypeArret.ASR,
                        jour_debut=debut,
                        jour_fin=fin,
                    )
                    for debut, fin in spec.arrets
                ],
                modulations=[
                    Modulation(
                        jour_debut=debut,
                        jour_fin=fin,
                        facteur=facteur,
                    )
                    for debut, fin, facteur in spec.modulations
                ],
            )
        )

    return Simulation(
        nom="animation",
        horizon_jours=HORIZON,
        prix_spot_eur_mwh=list(PRIX_SPOT_EUR_MWH),
        demande_nationale_mwh=list(DEMANDE_MWH),
        valeur_usage_eur_mwh=list(VALEUR_USAGE_EUR_MWH),
        tranches=entrees,
    )


def comparer(label: str, attendu, obtenu) -> None:
    if isinstance(attendu[0], (list, tuple)):
        plat_attendu = [valeur for ligne in attendu for valeur in ligne]
        plat_obtenu = [valeur for ligne in obtenu for valeur in ligne]
    else:
        plat_attendu = list(attendu)
        plat_obtenu = list(obtenu)

    if len(plat_attendu) != len(plat_obtenu):
        raise AssertionError(
            f"{label}: longueurs différentes {len(plat_attendu)} != {len(plat_obtenu)}"
        )

    for index, (a, b) in enumerate(zip(plat_attendu, plat_obtenu, strict=True)):
        if not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9):
            raise AssertionError(f"{label}[{index}]: {a} != {b}")

    print(f"OK {label}")


def main() -> None:
    resultat = SimulationEngine().run(construire_simulation())
    tranches = {t.tranche_id: t for t in resultat.tranches}

    comparer(
        "facteurs_reels",
        FACTEURS_REELS,
        tuple(
            tuple(tranches[spec.identifiant].facteurs_production) for spec in TRANCHES
        ),
    )
    comparer(
        "jepp_restant",
        JEPP_RESTANT,
        tuple(tuple(tranches[spec.identifiant].jepp_restant) for spec in TRANCHES),
    )
    comparer(
        "energie_mwh",
        ENERGIE_MWH,
        tuple(tuple(tranches[spec.identifiant].energie_mwh) for spec in TRANCHES),
    )
    comparer("offre_nationale_mwh", OFFRE_MWH, resultat.offre_nationale_mwh)
    if tuple(resultat.jours_deficit) != JOURS_DEFICIT:
        raise AssertionError(
            f"jours_deficit: {tuple(resultat.jours_deficit)} != {JOURS_DEFICIT}"
        )
    print(f"OK jours_deficit {JOURS_DEFICIT}")

    alertes = resultat.alertes
    neutronic = tuple(
        (alerte.jour, alerte.tranche_id)
        for alerte in alertes
        if alerte.type_alerte == TypeAlerte.NEUTRONIC_ANOMALY
    )
    if neutronic != ALERTES_NEUTRONIC:
        raise AssertionError(f"alertes neutronic: {neutronic} != {ALERTES_NEUTRONIC}")

    remit = {
        tranche_id: tuple(
            sorted(
                alerte.jour
                for alerte in alertes
                if alerte.type_alerte == TypeAlerte.REMIT_UMM
                and alerte.tranche_id == tranche_id
            )
        )
        for tranche_id, _ in ALERTES_REMIT
    }
    remit_attendu = dict(ALERTES_REMIT)
    if remit != remit_attendu:
        raise AssertionError(f"alertes REMIT: {remit} != {remit_attendu}")

    rte = tuple(
        alerte.jour
        for alerte in alertes
        if alerte.type_alerte == TypeAlerte.RTE_DEFICIT
    )
    if rte != ALERTES_RTE:
        raise AssertionError(f"alertes RTE: {rte} != {ALERTES_RTE}")

    spot = tuple(
        alerte.jour
        for alerte in alertes
        if alerte.type_alerte == TypeAlerte.SPOT_BELOW_USAGE_VALUE
    )
    if spot != ALERTES_SPOT:
        raise AssertionError(f"alertes spot: {spot} != {ALERTES_SPOT}")

    if len(alertes) != ALERTES_TOTAL:
        raise AssertionError(f"total alertes: {len(alertes)} != {ALERTES_TOTAL}")

    matrice = {
        type_alerte.value: tuple(
            sum(
                1
                for alerte in alertes
                if alerte.type_alerte == type_alerte and alerte.jour == jour
            )
            for jour in range(HORIZON)
        )
        for type_alerte in (
            TypeAlerte.NEUTRONIC_ANOMALY,
            TypeAlerte.REMIT_UMM,
            TypeAlerte.RTE_DEFICIT,
            TypeAlerte.SPOT_BELOW_USAGE_VALUE,
        )
    }
    if matrice != MATRICE_ALERTES:
        raise AssertionError(f"matrice alertes: {matrice} != {MATRICE_ALERTES}")

    print(f"OK alertes {ALERTES_TOTAL}")
    print("Exemple vérifié par le moteur CHAOURS.")


if __name__ == "__main__":
    main()
