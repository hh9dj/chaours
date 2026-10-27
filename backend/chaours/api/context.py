from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from chaours.db.models import SimulationTable
from chaours.db.repository import create_simulation
from chaours.db.session import (
    build_engine,
    build_session_factory,
    create_db_and_tables,
)
from chaours.demo import (
    DEMO_SIMULATION_ID,
    build_demo_simulation,
)


@dataclass(frozen=True, slots=True)
class AppContext:
    """Ressources partagées pendant toute la durée de vie de l'application."""

    engine: Engine
    session_factory: sessionmaker[Session]


def build_app_context(database_url: str | None = None) -> AppContext:
    """Construit le moteur SQLite, la fabrique de sessions et les tables."""
    app_engine = build_engine(database_url)
    session_factory = build_session_factory(app_engine)
    create_db_and_tables(app_engine)
    return AppContext(
        engine=app_engine,
        session_factory=session_factory,
    )


def ensure_demo_simulation(context: AppContext) -> bool:
    """Ajoute la démonstration par défaut si elle n'existe pas déjà."""
    with context.session_factory() as session:
        if session.get(SimulationTable, DEMO_SIMULATION_ID) is not None:
            return False
        create_simulation(
            session,
            build_demo_simulation(),
            simulation_id=DEMO_SIMULATION_ID,
        )
        return True


def create_lifespan(
    database_url: str | None = None,
    seed_demo: bool = True,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Construit le gestionnaire de cycle de vie de l'application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        context = build_app_context(database_url)
        if seed_demo:
            ensure_demo_simulation(context)
        app.state.context = context
        try:
            yield
        finally:
            context.engine.dispose()

    return lifespan
