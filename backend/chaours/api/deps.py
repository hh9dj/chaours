from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlmodel import Session


def get_session(request: Request) -> Generator[Session, None, None]:
    """Fournit une session SQLModel liée à la fabrique de l'application."""
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        yield session
