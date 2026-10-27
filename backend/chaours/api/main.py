import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from chaours.api.context import create_lifespan
from chaours.api.routes import simulations

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
        _pydantic_validation_handler,
    )
    application.include_router(simulations.router)
    return application


app = create_app()
