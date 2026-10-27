from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlmodel import SQLModel

import db.tables as _tables  # noqa: F401
from api.schemas import SimulationCreation
from core.models import SimulationNotFoundError
from db.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from db.repository import SimulationRepository
from services.simulations import SimulationService


@pytest.fixture
def service() -> Generator[SimulationService, None, None]:
    engine = build_engine("sqlite://")
    create_schema(engine, SQLModel.metadata)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        yield SimulationService(SimulationRepository(session))


def _payload() -> SimulationCreation:
    return SimulationCreation(
        nom="service-simulation",
        horizon_jours=2,
        prix_spot_eur_mwh=[10.0, 20.0],
        demande_nationale_mwh=[0.0, 0.0],
        valeur_usage_eur_mwh=[5.0, 5.0],
        tranches=[],
    )


def test_create_get_and_list(service: SimulationService):
    created = service.create(_payload())

    assert service.get(created.simulation_id).nom == "service-simulation"
    assert [item.nom for item in service.list_all()] == ["service-simulation"]


def test_get_unknown_simulation_raises(service: SimulationService):
    with pytest.raises(SimulationNotFoundError):
        service.get(uuid4())


def test_delete_unknown_simulation_raises(service: SimulationService):
    with pytest.raises(SimulationNotFoundError):
        service.delete(uuid4())


def test_run_returns_a_result(service: SimulationService):
    created = service.create(_payload())

    result = service.run(created.simulation_id)

    assert result.simulation_id == created.simulation_id
    assert len(result.demande_mwh) == 2
