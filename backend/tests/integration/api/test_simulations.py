from collections.abc import Generator
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.app import create_app
from api.context import AppContext
from core.models import TypeAlerte
from db.seed import DEMO_SIMULATION_NAME


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app = create_app("sqlite://", seed_demo=False)
    with TestClient(app) as test_client:
        yield test_client


def _payload() -> dict[str, Any]:
    return {
        "nom": "api-simulation",
        "horizon_jours": 5,
        "prix_spot_eur_mwh": [10.0, 80.0, 90.0, 100.0, 110.0],
        "demande_nationale_mwh": [0.0, 0.0, 0.0, 0.0, 0.0],
        "valeur_usage_eur_mwh": [60.0, 60.0, 60.0, 60.0, 60.0],
        "tranches": [
            {
                "tranche": {
                    "identifiant": "P1",
                    "code_eic": "EIC-P1",
                    "puissance_nominale_mw": 900.0,
                    "jepp_initial": 300.0,
                },
                "arrets": [
                    {"type_arret": "ASR", "jour_debut": 1, "jour_fin": 2}
                ],
                "modulations": [],
            },
            {
                "tranche": {
                    "identifiant": "P2",
                    "code_eic": "EIC-P2",
                    "puissance_nominale_mw": 1_300.0,
                    "jepp_initial": 280.0,
                },
                "arrets": [],
                "modulations": [
                    {"jour_debut": 2, "jour_fin": 4, "facteur": 0.5}
                ],
            },
        ],
    }


def _settings_payload() -> dict[str, Any]:
    return {
        "nom": "api-simulation-updated",
        "horizon_jours": 5,
        "prix_spot_eur_mwh": [11.0, 81.0, 91.0, 101.0, 111.0],
        "demande_nationale_mwh": [1.0, 1.0, 1.0, 1.0, 1.0],
        "valeur_usage_eur_mwh": [61.0, 61.0, 61.0, 61.0, 61.0],
    }


def _create(client: TestClient) -> dict[str, Any]:
    response = client.post("/simulations/", json=_payload())
    assert response.status_code == 201
    return response.json()


def test_list_simulations(client: TestClient):
    assert client.get("/simulations/").json() == []

    created = _create(client)
    response = client.get("/simulations/")

    assert response.status_code == 200
    summaries = response.json()
    assert len(summaries) == 1
    assert summaries[0]["simulation_id"] == created["simulation_id"]
    assert summaries[0]["nom"] == "api-simulation"
    assert summaries[0]["nombre_tranches"] == 2


def test_create_and_get_simulation(client: TestClient):
    created = _create(client)

    assert created["nom"] == "api-simulation"
    assert created["simulation_id"]
    assert created["cree_le"]

    fetched = client.get(f"/simulations/{created['simulation_id']}")
    assert fetched.status_code == 200
    assert fetched.json() == created


def test_create_generates_server_side_identifier(client: TestClient):
    payload = {**_payload(), "simulation_id": str(uuid4())}

    response = client.post("/simulations/", json=payload)

    assert response.status_code == 422


def test_get_unknown_simulation_returns_404(client: TestClient):
    response = client.get(f"/simulations/{uuid4()}")

    assert response.status_code == 404


def test_create_rejects_invalid_simulation(client: TestClient):
    payload = _payload()
    payload["tranches"][1]["tranche"]["identifiant"] = "P1"

    response = client.post("/simulations/", json=payload)

    assert response.status_code == 422


def test_create_rejects_series_length_mismatch(client: TestClient):
    payload = _payload()
    payload["valeur_usage_eur_mwh"] = [60.0, 60.0]

    response = client.post("/simulations/", json=payload)

    assert response.status_code == 422


def test_update_simulation_settings(client: TestClient):
    simulation_id = _create(client)["simulation_id"]

    response = client.put(
        f"/simulations/{simulation_id}",
        json=_settings_payload(),
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["nom"] == "api-simulation-updated"
    assert updated["prix_spot_eur_mwh"] == [11.0, 81.0, 91.0, 101.0, 111.0]
    assert updated["valeur_usage_eur_mwh"] == [61.0] * 5
    assert len(updated["tranches"]) == 2


def test_update_simulation_settings_rejects_bad_horizon(
    client: TestClient,
):
    simulation_id = _create(client)["simulation_id"]
    payload = _settings_payload()
    payload["horizon_jours"] = 6

    response = client.put(
        f"/simulations/{simulation_id}",
        json=payload,
    )

    assert response.status_code == 422


def test_update_simulation_settings_rejects_schedule_outside_horizon(
    client: TestClient,
):
    translation = _payload()
    translation["horizon_jours"] = 10
    translation["prix_spot_eur_mwh"] = [10.0] * 10
    translation["demande_nationale_mwh"] = [0.0] * 10
    translation["valeur_usage_eur_mwh"] = [60.0] * 10
    translation["tranches"][1]["arrets"] = [
        {"type_arret": "VD", "jour_debut": 7, "jour_fin": 9}
    ]
    simulation_id = client.post(
        "/simulations/",
        json=translation,
    ).json()["simulation_id"]
    payload = _settings_payload()

    response = client.put(
        f"/simulations/{simulation_id}",
        json=payload,
    )

    assert response.status_code == 422


def test_update_unknown_simulation_returns_404(client: TestClient):
    response = client.put(
        f"/simulations/{uuid4()}",
        json=_settings_payload(),
    )

    assert response.status_code == 404


def test_update_tranche_configuration(client: TestClient):
    simulation_id = _create(client)["simulation_id"]

    response = client.put(
        f"/simulations/{simulation_id}/plants/P1",
        json={
            "code_eic": "EIC-P1-NEW",
            "puissance_nominale_mw": 1_100.0,
            "jepp_initial": 250.0,
        },
    )

    assert response.status_code == 200
    tranche = response.json()["tranches"][0]["tranche"]
    assert tranche == {
        "identifiant": "P1",
        "code_eic": "EIC-P1-NEW",
        "puissance_nominale_mw": 1_100.0,
        "jepp_initial": 250.0,
    }


def test_update_tranche_rejects_invalid_configuration(
    client: TestClient,
):
    simulation_id = _create(client)["simulation_id"]

    response = client.put(
        f"/simulations/{simulation_id}/plants/P1",
        json={
            "code_eic": "",
            "puissance_nominale_mw": 0.0,
            "jepp_initial": -1.0,
        },
    )

    assert response.status_code == 422


def test_update_unknown_tranche_returns_404(client: TestClient):
    simulation_id = _create(client)["simulation_id"]

    response = client.put(
        f"/simulations/{simulation_id}/plants/UNKNOWN",
        json={
            "code_eic": "EIC-X",
            "puissance_nominale_mw": 900.0,
            "jepp_initial": 300.0,
        },
    )

    assert response.status_code == 404


def test_update_arrets(client: TestClient):
    simulation_id = _create(client)["simulation_id"]

    response = client.put(
        f"/simulations/{simulation_id}/plants/P1/maintenances",
        json=[{"type_arret": "VP", "jour_debut": 2, "jour_fin": 4}],
    )

    assert response.status_code == 200
    assert response.json()["tranches"][0]["arrets"] == [
        {"type_arret": "VP", "jour_debut": 2, "jour_fin": 4}
    ]
    fetched = client.get(f"/simulations/{simulation_id}").json()
    assert fetched["tranches"][0]["arrets"] == [
        {"type_arret": "VP", "jour_debut": 2, "jour_fin": 4}
    ]


def test_update_modulations(client: TestClient):
    simulation_id = _create(client)["simulation_id"]

    response = client.put(
        f"/simulations/{simulation_id}/plants/P2/modulations",
        json=[
            {"jour_debut": 1, "jour_fin": 3, "facteur": 0.25},
            {"jour_debut": 3, "jour_fin": 5, "facteur": 0.75},
        ],
    )

    assert response.status_code == 200
    assert response.json()["tranches"][1]["modulations"] == [
        {"jour_debut": 1, "jour_fin": 3, "facteur": 0.25},
        {"jour_debut": 3, "jour_fin": 5, "facteur": 0.75},
    ]


def test_update_arrets_rejects_overlap_with_422(client: TestClient):
    simulation_id = _create(client)["simulation_id"]

    response = client.put(
        f"/simulations/{simulation_id}/plants/P1/maintenances",
        json=[
            {"type_arret": "ASR", "jour_debut": 1, "jour_fin": 4},
            {"type_arret": "VP", "jour_debut": 3, "jour_fin": 5},
        ],
    )

    assert response.status_code == 422
    fetched = client.get(f"/simulations/{simulation_id}").json()
    assert fetched["tranches"][0]["arrets"] == [
        {"type_arret": "ASR", "jour_debut": 1, "jour_fin": 2}
    ]


def test_update_arrets_outside_horizon_returns_422(client: TestClient):
    simulation_id = _create(client)["simulation_id"]

    response = client.put(
        f"/simulations/{simulation_id}/plants/P1/maintenances",
        json=[{"type_arret": "ASR", "jour_debut": 1, "jour_fin": 6}],
    )

    assert response.status_code == 422


def test_update_modulations_rejects_overlap_with_422(
    client: TestClient,
):
    simulation_id = _create(client)["simulation_id"]

    response = client.put(
        f"/simulations/{simulation_id}/plants/P2/modulations",
        json=[
            {"jour_debut": 1, "jour_fin": 4, "facteur": 0.25},
            {"jour_debut": 3, "jour_fin": 5, "facteur": 0.75},
        ],
    )

    assert response.status_code == 422
    fetched = client.get(f"/simulations/{simulation_id}").json()
    assert fetched["tranches"][1]["modulations"] == [
        {"jour_debut": 2, "jour_fin": 4, "facteur": 0.5}
    ]


def test_update_unknown_simulation_schedule_returns_404(
    client: TestClient,
):
    response = client.put(
        f"/simulations/{uuid4()}/plants/P1/maintenances",
        json=[],
    )

    assert response.status_code == 404


def test_update_unknown_plant_schedule_returns_404(
    client: TestClient,
):
    simulation_id = _create(client)["simulation_id"]

    response = client.put(
        f"/simulations/{simulation_id}/plants/UNKNOWN/maintenances",
        json=[],
    )

    assert response.status_code == 404


def test_run_simulation(client: TestClient):
    simulation_id = _create(client)["simulation_id"]

    response = client.post(f"/simulations/{simulation_id}/run")

    assert response.status_code == 200
    result = response.json()
    assert result["simulation_id"] == simulation_id
    assert len(result["tranches"]) == 2
    assert len(result["offre_nationale_mwh"]) == 5
    assert len(result["demande_mwh"]) == 5
    assert result["tranches"][0]["facteurs_production"][1] == 0.0
    assert result["duree_execution_ms"] >= 0.0
    spot_alerts = [
        alerte
        for alerte in result["alertes"]
        if alerte["type_alerte"] == "SPOT_BELOW_USAGE_VALUE"
    ]
    assert [alerte["jour"] for alerte in spot_alerts] == [0]
    assert all(alerte["tranche_id"] is None for alerte in spot_alerts)


def test_run_unknown_simulation_returns_404(client: TestClient):
    response = client.post(f"/simulations/{uuid4()}/run")

    assert response.status_code == 404


def test_delete_simulation(client: TestClient):
    simulation_id = _create(client)["simulation_id"]

    response = client.delete(f"/simulations/{simulation_id}")

    assert response.status_code == 204
    assert client.get(f"/simulations/{simulation_id}").status_code == 404
    assert client.delete(f"/simulations/{simulation_id}").status_code == 404


def test_lifespan_exposes_typed_app_context(client: TestClient):
    application = cast(FastAPI, client.app)
    context = application.state.context

    assert isinstance(context, AppContext)
    assert context.session_factory is not None


def test_create_simulation_without_tranches(client: TestClient):
    payload = _payload()
    payload["tranches"] = []

    response = client.post("/simulations/", json=payload)

    assert response.status_code == 201
    created = response.json()
    assert created["tranches"] == []
    assert client.get(
        f"/simulations/{created['simulation_id']}"
    ).json()["tranches"] == []

    summaries = client.get("/simulations/").json()
    assert summaries[0]["nombre_tranches"] == 0

    result = client.post(
        f"/simulations/{created['simulation_id']}/run"
    ).json()
    assert result["tranches"] == []
    assert result["offre_nationale_mwh"] == [0.0] * 5


def _tranche_payload(
    identifiant: str = "P3",
    jour_debut: int = 0,
    jour_fin: int = 2,
) -> dict[str, Any]:
    return {
        "tranche": {
            "identifiant": identifiant,
            "code_eic": f"EIC-{identifiant}",
            "puissance_nominale_mw": 900.0,
            "jepp_initial": 300.0,
        },
        "arrets": [
            {
                "type_arret": "ASR",
                "jour_debut": jour_debut,
                "jour_fin": jour_fin,
            }
        ],
        "modulations": [],
    }


def test_add_tranche_to_empty_simulation(client: TestClient):
    payload = _payload()
    payload["tranches"] = []
    simulation_id = client.post(
        "/simulations/",
        json=payload,
    ).json()["simulation_id"]

    response = client.post(
        f"/simulations/{simulation_id}/plants",
        json=_tranche_payload(),
    )

    assert response.status_code == 201
    added = response.json()["tranches"]
    assert len(added) == 1
    assert added[0]["tranche"]["identifiant"] == "P3"
    fetched = client.get(f"/simulations/{simulation_id}").json()
    assert fetched["tranches"][0]["tranche"]["identifiant"] == "P3"
    result = client.post(
        f"/simulations/{simulation_id}/run"
    ).json()
    assert len(result["tranches"]) == 1


def test_add_tranche_rejects_duplicate_with_422(client: TestClient):
    simulation_id = _create(client)["simulation_id"]

    response = client.post(
        f"/simulations/{simulation_id}/plants",
        json=_tranche_payload(identifiant="P1"),
    )

    assert response.status_code == 422
    fetched = client.get(f"/simulations/{simulation_id}").json()
    assert [
        entry["tranche"]["identifiant"] for entry in fetched["tranches"]
    ] == ["P1", "P2"]


def test_add_tranche_outside_horizon_returns_422(client: TestClient):
    payload = _payload()
    payload["tranches"] = []
    simulation_id = client.post(
        "/simulations/",
        json=payload,
    ).json()["simulation_id"]

    response = client.post(
        f"/simulations/{simulation_id}/plants",
        json=_tranche_payload(jour_debut=1, jour_fin=6),
    )

    assert response.status_code == 422


def test_add_tranche_unknown_simulation_returns_404(
    client: TestClient,
):
    response = client.post(
        f"/simulations/{uuid4()}/plants",
        json=_tranche_payload(),
    )

    assert response.status_code == 404


def test_create_app_seeds_demo_simulation_with_all_alerts():
    app = create_app("sqlite://", seed_demo=True)

    with TestClient(app) as demo_client:
        simulations = demo_client.get("/simulations/").json()

        assert len(simulations) == 1
        assert simulations[0]["nom"] == DEMO_SIMULATION_NAME
        result = demo_client.post(
            f"/simulations/{simulations[0]['simulation_id']}/run"
        ).json()

    assert {alerte["type_alerte"] for alerte in result["alertes"]} == {
        type_alerte.value for type_alerte in TypeAlerte
    }


def test_demo_seed_is_idempotent(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'demo.db').as_posix()}"

    for _ in range(2):
        app = create_app(database_url, seed_demo=True)
        with TestClient(app) as demo_client:
            assert len(demo_client.get("/simulations/").json()) == 1
