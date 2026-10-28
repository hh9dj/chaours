import json
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlmodel import SQLModel

import db.tables as _tables  # noqa: F401
from api.config import LOCAL_FRONTEND_ORIGINS
from api.context import AppContext
from api.routers import simulations
from core.models import SimulationNotFoundError, TrancheNotFoundError
from db.database import build_db_context, create_schema
from db.seed import ensure_demo_simulation


def build_app_context(database_url: str | None = None) -> AppContext:
    """Construit le moteur SQLite, la fabrique de sessions et les tables."""
    context = build_db_context(database_url)
    create_schema(context.engine, SQLModel.metadata)
    return context


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


async def pydantic_validation_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Traduit une validation Pydantic hors requête en réponse 422."""
    if not isinstance(exc, ValidationError):
        raise exc
    return JSONResponse(
        status_code=422,
        content={"detail": json.loads(exc.json())},
    )


async def simulation_not_found_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Traduit une simulation absente en réponse 404."""
    if not isinstance(exc, SimulationNotFoundError):
        raise exc
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Simulation introuvable"},
    )


async def tranche_not_found_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Traduit une tranche absente en réponse 404."""
    if not isinstance(exc, TrancheNotFoundError):
        raise exc
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Simulation ou tranche introuvable"},
    )


# TODO: add logging middleware.
def create_app(
    database_url: str | None = None,
    seed_demo: bool = True,
) -> FastAPI:
    """Construit l'application et configure son cycle de vie."""
    application = FastAPI(
        title="CHAOURS API",
        version="0.1.0",
        description="API de simulation des arrêts nucléaires.",
        lifespan=create_lifespan(database_url, seed_demo=seed_demo),
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=LOCAL_FRONTEND_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_exception_handler(
        ValidationError,
        pydantic_validation_handler,
    )
    application.add_exception_handler(
        SimulationNotFoundError,
        simulation_not_found_handler,
    )
    application.add_exception_handler(
        TrancheNotFoundError,
        tranche_not_found_handler,
    )
    application.include_router(simulations.router)
    return application


app = create_app()
