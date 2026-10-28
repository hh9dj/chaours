from dataclasses import dataclass

HORIZON = 7
JOURS = tuple(f"J{jour}" for jour in range(HORIZON))


@dataclass(frozen=True)
class TrancheSpec:
    identifiant: str
    puissance_mw: float
    jepp_initial: float
    arrets: tuple[tuple[int, int], ...]
    modulations: tuple[tuple[int, int, float], ...]


TRANCHES = (
    TrancheSpec(
        identifiant="P1",
        puissance_mw=1_000.0,
        jepp_initial=2.5,
        arrets=((4, 6),),
        modulations=((1, 3, 0.5),),
    ),
    TrancheSpec(
        identifiant="P2",
        puissance_mw=1_300.0,
        jepp_initial=10.0,
        arrets=((3, 5),),
        modulations=((1, 4, 0.8),),
    ),
    TrancheSpec(
        identifiant="P3",
        puissance_mw=900.0,
        jepp_initial=10.0,
        arrets=(),
        modulations=((3, 5, 0.6),),
    ),
)

DEMANDE_MWH = (
    75_000.0,
    70_000.0,
    60_000.0,
    50_000.0,
    45_000.0,
    50_000.0,
    74_000.0,
)
PRIX_SPOT_EUR_MWH = (40.0, 60.0, 90.0, 70.0, 30.0, 120.0, 110.0)
VALEUR_USAGE_EUR_MWH = (50.0, 55.0, 80.0, 80.0, 60.0, 100.0, 90.0)

FACTEURS_MODULES = (
    (1.0, 0.5, 0.5, 1.0, 1.0, 1.0, 1.0),
    (1.0, 0.8, 0.8, 0.8, 1.0, 1.0, 1.0),
    (1.0, 1.0, 1.0, 0.6, 0.6, 1.0, 1.0),
)

FACTEURS_DEMANDES = (
    (1.0, 0.5, 0.5, 1.0, 0.0, 0.0, 1.0),
    (1.0, 0.8, 0.8, 0.0, 0.0, 1.0, 1.0),
    (1.0, 1.0, 1.0, 0.6, 0.6, 1.0, 1.0),
)

FACTEURS_REELS = (
    (1.0, 0.5, 0.5, 0.5, 0.0, 0.0, 1.0),
    (1.0, 0.8, 0.8, 0.0, 0.0, 1.0, 1.0),
    (1.0, 1.0, 1.0, 0.6, 0.6, 1.0, 1.0),
)

JEPP_RESTANT = (
    (1.5, 1.0, 0.5, 0.0, 0.0, 0.0, 1.5),
    (9.0, 8.2, 7.4, 7.4, 7.4, 9.0, 8.0),
    (9.0, 8.0, 7.0, 6.4, 5.8, 4.8, 3.8),
)

ENERGIE_MWH = (
    (24_000.0, 12_000.0, 12_000.0, 12_000.0, 0.0, 0.0, 24_000.0),
    (31_200.0, 24_960.0, 24_960.0, 0.0, 0.0, 31_200.0, 31_200.0),
    (21_600.0, 21_600.0, 21_600.0, 12_960.0, 12_960.0, 21_600.0, 21_600.0),
)

OFFRE_MWH = (
    76_800.0,
    58_560.0,
    58_560.0,
    24_960.0,
    12_960.0,
    52_800.0,
    76_800.0,
)
JOURS_DEFICIT = (1, 2, 3, 4)

ALERTES_NEUTRONIC = ((3, "P1"),)
ALERTES_REMIT = (
    ("P1", (1, 4, 6)),
    ("P2", (1, 3, 5)),
    ("P3", (3, 5)),
)
ALERTES_RTE = (1, 2, 3, 4)
ALERTES_SPOT = (0, 3, 4)
ALERTES_TOTAL = 16

MATRICE_ALERTES = {
    "NEUTRONIC_ANOMALY": (0, 0, 0, 1, 0, 0, 0),
    "REMIT_UMM": (0, 2, 0, 2, 1, 2, 1),
    "RTE_DEFICIT": (0, 1, 1, 1, 1, 0, 0),
    "SPOT_BELOW_USAGE_VALUE": (1, 0, 0, 1, 1, 0, 0),
}


def format_mwh(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def format_factor(value: float) -> str:
    return f"{value:.2f}"


def format_jepp(value: float) -> str:
    return f"{value:.1f}"
