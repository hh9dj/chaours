from __future__ import annotations

import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from chaours.api.routes import simulations
from chaours.db.session import (
    build_engine,
    build_session_factory,
    create_db_and_tables,
)

LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]


async def _pydantic_validation_handler(
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


def create_app(database_url: str | None = None) -> FastAPI:
    """Construit l'application et initialise la base SQLite."""
    app_engine = build_engine(database_url)
    session_factory = build_session_factory(app_engine)
    create_db_and_tables(app_engine)

    application = FastAPI(
        title="CHAOURS API",
        version="0.1.0",
        description="API de simulation des arrêts nucléaires.",
    )
    application.state.engine = app_engine
    application.state.session_factory = session_factory

    application.add_middleware(
        CORSMiddleware,
        allow_origins=LOCAL_FRONTEND_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_exception_handler(
        ValidationError,
        _pydantic_validation_handler,
    )
    application.include_router(simulations.router)
    return application


app = create_app()
