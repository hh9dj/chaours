from __future__ import annotations

import os
from typing import Any

from sqlalchemy import Engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from chaours.db import models as _models  # noqa: F401  (metadata registration)

DEFAULT_DATABASE_URL = "sqlite:///./chaours.db"


def resolve_database_url(database_url: str | None = None) -> str:
    """Renvoie l'URL de base demandée, sinon la variable d'environnement."""
    if database_url is not None:
        return database_url
    return os.environ.get("CHAOURS_DATABASE_URL", DEFAULT_DATABASE_URL)


def _enable_sqlite_foreign_keys(
    dbapi_connection: Any,
    _connection_record: Any,
) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def build_engine(database_url: str | None = None) -> Engine:
    """Construit un moteur SQLAlchemy pour SQLite."""
    url = resolve_database_url(database_url)
    kwargs: dict[str, Any] = {}

    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"} or ":memory:" in url:
            kwargs["poolclass"] = StaticPool

    engine = create_engine(url, **kwargs)

    if url.startswith("sqlite"):
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)

    return engine


def build_session_factory(
    engine: Engine,
) -> sessionmaker[Session]:
    """Construit une fabrique de sessions liée au moteur donné."""
    return sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )


def create_db_and_tables(target_engine: Engine) -> None:
    """Crée les tables SQLModel manquantes sur le moteur donné."""
    SQLModel.metadata.create_all(target_engine)


__all__ = [
    "DEFAULT_DATABASE_URL",
    "Session",
    "build_engine",
    "build_session_factory",
    "create_db_and_tables",
    "resolve_database_url",
]
