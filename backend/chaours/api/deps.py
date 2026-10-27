from collections.abc import Generator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlmodel import Session

from chaours.api.context import AppContext


def get_context(request: Request) -> AppContext:
    """Renvoie le contexte applicatif typé, créé au démarrage."""
    return cast(AppContext, request.app.state.context)


def get_session(
    context: Annotated[AppContext, Depends(get_context)],
) -> Generator[Session, None, None]:
    """Fournit une session SQLModel liée au contexte de l'application."""
    with context.session_factory() as session:
        yield session
