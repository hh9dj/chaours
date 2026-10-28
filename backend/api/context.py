from dataclasses import dataclass
from typing import cast

from fastapi import Request
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session


@dataclass(frozen=True, slots=True)
class AppContext:
    """Ressources partagées pendant toute la durée de vie de l'application."""

    engine: Engine
    session_factory: sessionmaker[Session]


def get_context(request: Request) -> AppContext:
    """Renvoie le contexte applicatif typé, créé au démarrage."""
    return cast(AppContext, request.app.state.context)
