from __future__ import annotations

import math
from datetime import timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from chaours.types import (
    Alerte,
    Arret,
    Modulation,
    ResultatSimulation,
    ResultatTranche,
    Simulation,
    SimulationTranche,
    Tranche,
    TypeAlerte,
    TypeArret,
)


def _tranche(identifiant: str = "P1") -> Tranche:
    return Tranche(
        identifiant=identifiant,
        code_eic=f"EIC-{identifiant}",
        puissance_nominale_mw=900.0,
        jepp_initial=300.0,
    )


def _entry(
    identifiant: str = "P1",
    arrets: list[Arret] | None = None,
    modulations: list[Modulation] | None = None,
) -> SimulationTranche:
    return SimulationTranche(
        tranche=_tranche(identifiant),
        arrets=list(arrets or []),
        modulations=list(modulations or []),
    )


def _simulation(**overrides: Any) -> Simulation:
    data: dict[str, Any] = {
        "nom": "simulation",
        "horizon_jours": 4,
        "prix_spot_eur_mwh": [80.0, 80.0, 80.0, 80.0],
        "demande_nationale_mwh": [0.0, 0.0, 0.0, 0.0],
        "valeur_usage_eur_mwh": [60.0, 60.0, 60.0, 60.0],
        "tranches": [_entry()],
    }
    data.update(overrides)
    return Simulation(**data)


def _resultat_tranche(**overrides: Any) -> ResultatTranche:
    data: dict[str, Any] = {
        "tranche_id": "P1",
        "facteurs_production": [1.0, 0.5],
        "energie_mwh": [100.0, 50.0],
        "jepp_restant": [10.0, 5.0],
        "jours_epuisement": [],
    }
    data.update(overrides)
    return ResultatTranche(**data)


def _resultat_simulation(**overrides: Any) -> ResultatSimulation:
    data: dict[str, Any] = {
        "simulation_id": uuid4(),
        "duree_execution_ms": 1.0,
        "tranches": [_resultat_tranche()],
        "offre_nationale_mwh": [100.0, 50.0],
        "demande_mwh": [0.0, 0.0],
        "jours_deficit": [],
        "alertes": [],
    }
    data.update(overrides)
    return ResultatSimulation(**data)


def test_simulation_defaults_generate_uuid_and_utc_timestamp():
    simulation = _simulation()

    assert isinstance(simulation.simulation_id, UUID)
    assert simulation.cree_le.tzinfo == timezone.utc


def test_tranche_rejects_empty_ids_and_invalid_values():
    with pytest.raises(ValidationError):
        Tranche(
            identifiant="",
            code_eic="EIC",
            puissance_nominale_mw=900.0,
            jepp_initial=300.0,
        )
    with pytest.raises(ValidationError):
        Tranche(
            identifiant="P1",
            code_eic="",
            puissance_nominale_mw=900.0,
            jepp_initial=300.0,
        )
    with pytest.raises(ValidationError):
        Tranche(
            identifiant="P1",
            code_eic="EIC",
            puissance_nominale_mw=0.0,
            jepp_initial=300.0,
        )
    with pytest.raises(ValidationError):
        Tranche(
            identifiant="P1",
            code_eic="EIC",
            puissance_nominale_mw=900.0,
            jepp_initial=-1.0,
        )


@pytest.mark.parametrize(
    "arret",
    [
        {"type_arret": "ASR", "jour_debut": -1, "jour_fin": 2},
        {"type_arret": "ASR", "jour_debut": 2, "jour_fin": 2},
        {"type_arret": "ASR", "jour_debut": 3, "jour_fin": 2},
    ],
)
def test_arret_rejects_invalid_windows(arret: dict[str, Any]):
    with pytest.raises(ValidationError):
        Arret(**arret)


@pytest.mark.parametrize(
    "modulation",
    [
        {"jour_debut": -1, "jour_fin": 2, "facteur": 0.5},
        {"jour_debut": 2, "jour_fin": 2, "facteur": 0.5},
        {"jour_debut": 3, "jour_fin": 2, "facteur": 0.5},
        {"jour_debut": 0, "jour_fin": 2, "facteur": -0.1},
        {"jour_debut": 0, "jour_fin": 2, "facteur": 1.1},
        {"jour_debut": 0, "jour_fin": 2, "facteur": math.nan},
    ],
)
def test_modulation_rejects_invalid_windows_and_factors(
    modulation: dict[str, Any],
):
    with pytest.raises(ValidationError):
        Modulation(**modulation)


def test_models_reject_extra_fields():
    with pytest.raises(ValidationError):
        Tranche.model_validate(
            {
                "identifiant": "P1",
                "code_eic": "EIC",
                "puissance_nominale_mw": 900.0,
                "jepp_initial": 300.0,
                "extra": 1,
            }
        )


def test_simulation_rejects_overlapping_arrets():
    with pytest.raises(ValidationError):
        _entry(
            arrets=[
                Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=4),
                Arret(type_arret=TypeArret.VP, jour_debut=3, jour_fin=5),
            ]
        )


def test_simulation_allows_touching_arrets():
    entry = _entry(
        arrets=[
            Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3),
            Arret(type_arret=TypeArret.VP, jour_debut=3, jour_fin=5),
        ]
    )

    assert len(entry.arrets) == 2


def test_simulation_rejects_overlapping_modulations():
    with pytest.raises(ValidationError):
        _entry(
            modulations=[
                Modulation(jour_debut=1, jour_fin=4, facteur=0.5),
                Modulation(jour_debut=3, jour_fin=5, facteur=0.6),
            ]
        )


def test_simulation_allows_touching_modulations():
    entry = _entry(
        modulations=[
            Modulation(jour_debut=1, jour_fin=3, facteur=0.5),
            Modulation(jour_debut=3, jour_fin=5, facteur=0.6),
        ]
    )

    assert len(entry.modulations) == 2


@pytest.mark.parametrize("horizon_jours", [0, -1, 7306])
def test_simulation_rejects_invalid_horizon(horizon_jours: int):
    with pytest.raises(ValidationError):
        _simulation(horizon_jours=horizon_jours)


def test_simulation_accepts_maximum_horizon():
    horizon = 7305
    simulation = _simulation(
        horizon_jours=horizon,
        prix_spot_eur_mwh=[80.0] * horizon,
        demande_nationale_mwh=[0.0] * horizon,
        valeur_usage_eur_mwh=[60.0] * horizon,
    )

    assert simulation.horizon_jours == horizon


def test_simulation_allows_empty_tranche_list():
    simulation = _simulation(tranches=[])

    assert simulation.tranches == []


def test_simulation_requires_unique_tranche_ids():
    with pytest.raises(ValidationError):
        _simulation(tranches=[_entry("P1"), _entry("P1")])


def test_simulation_requires_series_lengths_to_match_horizon():
    with pytest.raises(ValidationError):
        _simulation(prix_spot_eur_mwh=[80.0] * 3)
    with pytest.raises(ValidationError):
        _simulation(demande_nationale_mwh=[0.0] * 3)
    with pytest.raises(ValidationError):
        _simulation(valeur_usage_eur_mwh=[60.0] * 3)


@pytest.mark.parametrize(
    "overrides",
    [
        {"prix_spot_eur_mwh": [80.0, math.inf, 80.0, 80.0]},
        {"prix_spot_eur_mwh": [80.0, math.nan, 80.0, 80.0]},
        {"demande_nationale_mwh": [0.0, math.inf, 0.0, 0.0]},
        {"demande_nationale_mwh": [0.0, math.nan, 0.0, 0.0]},
        {"valeur_usage_eur_mwh": [60.0, math.inf, 60.0, 60.0]},
        {"valeur_usage_eur_mwh": [60.0, math.nan, 60.0, 60.0]},
    ],
)
def test_simulation_rejects_non_finite_values(overrides: dict[str, Any]):
    with pytest.raises(ValidationError):
        _simulation(**overrides)


def test_simulation_rejects_negative_demand():
    with pytest.raises(ValidationError):
        _simulation(demande_nationale_mwh=[0.0, -1.0, 0.0, 0.0])


def test_simulation_rejects_windows_outside_the_horizon():
    with pytest.raises(ValidationError):
        _simulation(
            tranches=[
                _entry(
                    arrets=[
                        Arret(
                            type_arret=TypeArret.ASR,
                            jour_debut=1,
                            jour_fin=5,
                        )
                    ],
                )
            ]
        )
    with pytest.raises(ValidationError):
        _simulation(
            tranches=[
                _entry(
                    modulations=[
                        Modulation(
                            jour_debut=1,
                            jour_fin=5,
                            facteur=0.5,
                        )
                    ]
                )
            ]
        )


def test_simulation_validation_runs_on_assignment():
    simulation = _simulation()

    with pytest.raises(ValidationError):
        simulation.horizon_jours = 0


def test_resultat_tranche_rejects_invalid_production_factors():
    with pytest.raises(ValidationError):
        _resultat_tranche(facteurs_production=[1.0, 1.5])
    with pytest.raises(ValidationError):
        _resultat_tranche(facteurs_production=[-0.1, 0.5])
    with pytest.raises(ValidationError):
        _resultat_tranche(facteurs_production=[math.nan, 0.5])
    with pytest.raises(ValidationError):
        _resultat_tranche(facteurs_production=[math.inf, 0.5])


def test_resultat_tranche_rejects_negative_or_non_finite_arrays():
    with pytest.raises(ValidationError):
        _resultat_tranche(energie_mwh=[100.0, -1.0])
    with pytest.raises(ValidationError):
        _resultat_tranche(jepp_restant=[10.0, -1.0])
    with pytest.raises(ValidationError):
        _resultat_tranche(energie_mwh=[100.0, math.inf])
    with pytest.raises(ValidationError):
        _resultat_tranche(jepp_restant=[10.0, math.nan])


def test_resultat_tranche_requires_ascending_depletion_days():
    with pytest.raises(ValidationError):
        _resultat_tranche(jours_epuisement=[1, 0])


def test_resultat_tranche_requires_equal_array_lengths():
    with pytest.raises(ValidationError):
        _resultat_tranche(energie_mwh=[100.0])


def test_resultat_simulation_requires_matching_supply_and_demand():
    with pytest.raises(ValidationError):
        _resultat_simulation(offre_nationale_mwh=[100.0])


def test_resultat_simulation_requires_tranche_arrays_to_match_horizon():
    with pytest.raises(ValidationError):
        _resultat_simulation(
            tranches=[
                _resultat_tranche(
                    facteurs_production=[1.0],
                    energie_mwh=[100.0],
                    jepp_restant=[10.0],
                )
            ]
        )


def test_resultat_simulation_rejects_days_outside_horizon():
    with pytest.raises(ValidationError):
        _resultat_simulation(jours_deficit=[2])
    with pytest.raises(ValidationError):
        _resultat_simulation(
            tranches=[_resultat_tranche(jours_epuisement=[2])]
        )
    with pytest.raises(ValidationError):
        _resultat_simulation(
            alertes=[
                Alerte(
                    type_alerte=TypeAlerte.REMIT_UMM,
                    jour=2,
                    tranche_id="P1",
                    message="Alerte.",
                )
            ]
        )


def test_resultat_simulation_requires_unique_tranche_ids():
    with pytest.raises(ValidationError):
        _resultat_simulation(
            tranches=[_resultat_tranche(), _resultat_tranche()]
        )


def test_resultat_simulation_rejects_negative_execution_time():
    with pytest.raises(ValidationError):
        _resultat_simulation(duree_execution_ms=-1.0)


def test_resultat_simulation_accepts_alerts_without_day():
    result = _resultat_simulation(
        alertes=[
            Alerte(
                type_alerte=TypeAlerte.NEUTRONIC_ANOMALY,
                jour=None,
                tranche_id="P1",
                message="Alerte.",
            )
        ]
    )

    assert result.alertes[0].jour is None
