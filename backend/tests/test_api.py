from __future__ import annotations

from collections.abc import Generator
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from chaours.api.main import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app = create_app("sqlite://")
    with TestClient(app) as test_client:
        yield test_client


def _payload() -> dict[str, Any]:
    return {
        "name": "api-scenario",
        "horizon_days": 5,
        "spot_prices": [10.0, 80.0, 90.0, 100.0, 110.0],
        "demand_mwh": [0.0, 0.0, 0.0, 0.0, 0.0],
        "usage_values_eur_mwh": {"P1": 60.0, "P2": 70.0},
        "plants": [
            {
                "plant": {
                    "id": "P1",
                    "eic_code": "EIC-P1",
                    "nominal_power_mw": 900.0,
                    "initial_jepp": 300.0,
                },
                "maintenances": [
                    {"kind": "ASR", "start_day": 1, "end_day": 2}
                ],
                "modulations": [],
            },
            {
                "plant": {
                    "id": "P2",
                    "eic_code": "EIC-P2",
                    "nominal_power_mw": 1_300.0,
                    "initial_jepp": 280.0,
                },
                "maintenances": [],
                "modulations": [{"start_day": 2, "end_day": 4, "factor": 0.5}],
            },
        ],
    }


def test_create_and_get_simulation(client: TestClient):
    response = client.post("/simulations/", json=_payload())

    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "api-scenario"
    assert created["scenario_id"]
    assert created["created_at"]

    fetched = client.get(f"/simulations/{created['scenario_id']}")
    assert fetched.status_code == 200
    assert fetched.json() == created


def test_create_generates_server_side_identifier(client: TestClient):
    supplied_id = str(uuid4())
    payload = {**_payload(), "scenario_id": supplied_id}

    response = client.post("/simulations/", json=payload)

    assert response.status_code == 201
    assert response.json()["scenario_id"] != supplied_id


def test_get_unknown_simulation_returns_404(client: TestClient):
    response = client.get(f"/simulations/{uuid4()}")

    assert response.status_code == 404


def test_create_rejects_invalid_scenario(client: TestClient):
    payload = _payload()
    payload["plants"][1]["plant"]["id"] = "P1"

    response = client.post("/simulations/", json=payload)

    assert response.status_code == 422


def test_update_maintenances(client: TestClient):
    scenario_id = client.post("/simulations/", json=_payload()).json()[
        "scenario_id"
    ]

    response = client.put(
        f"/simulations/{scenario_id}/plants/P1/maintenances",
        json=[{"kind": "VP", "start_day": 2, "end_day": 4}],
    )

    assert response.status_code == 200
    plants = response.json()["plants"]
    assert plants[0]["maintenances"] == [
        {"kind": "VP", "start_day": 2, "end_day": 4}
    ]
    fetched = client.get(f"/simulations/{scenario_id}").json()
    assert fetched["plants"][0]["maintenances"] == [
        {"kind": "VP", "start_day": 2, "end_day": 4}
    ]


def test_update_modulations(client: TestClient):
    scenario_id = client.post("/simulations/", json=_payload()).json()[
        "scenario_id"
    ]

    response = client.put(
        f"/simulations/{scenario_id}/plants/P2/modulations",
        json=[
            {"start_day": 1, "end_day": 3, "factor": 0.25},
            {"start_day": 3, "end_day": 5, "factor": 0.75},
        ],
    )

    assert response.status_code == 200
    assert response.json()["plants"][1]["modulations"] == [
        {"start_day": 1, "end_day": 3, "factor": 0.25},
        {"start_day": 3, "end_day": 5, "factor": 0.75},
    ]


def test_update_maintenances_rejects_overlap_with_422(client: TestClient):
    scenario_id = client.post("/simulations/", json=_payload()).json()[
        "scenario_id"
    ]

    response = client.put(
        f"/simulations/{scenario_id}/plants/P1/maintenances",
        json=[
            {"kind": "ASR", "start_day": 1, "end_day": 4},
            {"kind": "VP", "start_day": 3, "end_day": 5},
        ],
    )

    assert response.status_code == 422
    fetched = client.get(f"/simulations/{scenario_id}").json()
    assert fetched["plants"][0]["maintenances"] == [
        {"kind": "ASR", "start_day": 1, "end_day": 2}
    ]


def test_update_schedule_outside_horizon_returns_422(client: TestClient):
    scenario_id = client.post("/simulations/", json=_payload()).json()[
        "scenario_id"
    ]

    response = client.put(
        f"/simulations/{scenario_id}/plants/P1/maintenances",
        json=[{"kind": "ASR", "start_day": 1, "end_day": 6}],
    )

    assert response.status_code == 422


def test_update_unknown_scenario_returns_404(client: TestClient):
    response = client.put(
        f"/simulations/{uuid4()}/plants/P1/maintenances",
        json=[],
    )

    assert response.status_code == 404


def test_update_unknown_plant_returns_404(client: TestClient):
    scenario_id = client.post("/simulations/", json=_payload()).json()[
        "scenario_id"
    ]

    response = client.put(
        f"/simulations/{scenario_id}/plants/UNKNOWN/maintenances",
        json=[],
    )

    assert response.status_code == 404


def test_run_simulation(client: TestClient):
    scenario_id = client.post("/simulations/", json=_payload()).json()[
        "scenario_id"
    ]

    response = client.post(f"/simulations/{scenario_id}/run")

    assert response.status_code == 200
    result = response.json()
    assert result["scenario_id"] == scenario_id
    assert len(result["plants"]) == 2
    assert len(result["national_supply_mwh"]) == 5
    assert len(result["demand_mwh"]) == 5
    assert result["plants"][0]["production_factors"][1] == 0.0
    assert result["execution_time_ms"] >= 0.0


def test_run_unknown_simulation_returns_404(client: TestClient):
    response = client.post(f"/simulations/{uuid4()}/run")

    assert response.status_code == 404


def test_delete_simulation(client: TestClient):
    scenario_id = client.post("/simulations/", json=_payload()).json()[
        "scenario_id"
    ]

    response = client.delete(f"/simulations/{scenario_id}")

    assert response.status_code == 204
    assert client.get(f"/simulations/{scenario_id}").status_code == 404
    assert client.delete(f"/simulations/{scenario_id}").status_code == 404


def test_update_modulations_rejects_overlap_with_422(client: TestClient):
    scenario_id = client.post("/simulations/", json=_payload()).json()[
        "scenario_id"
    ]

    response = client.put(
        f"/simulations/{scenario_id}/plants/P2/modulations",
        json=[
            {"start_day": 1, "end_day": 4, "factor": 0.25},
            {"start_day": 3, "end_day": 5, "factor": 0.75},
        ],
    )

    assert response.status_code == 422
    fetched = client.get(f"/simulations/{scenario_id}").json()
    assert fetched["plants"][1]["modulations"] == [
        {"start_day": 2, "end_day": 4, "factor": 0.5}
    ]
