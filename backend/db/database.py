from collections.abc import Generator
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import Engine, MetaData, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from api.context import AppContext, get_context
from db.config import resolve_database_url


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

    if url.startswith("sqlite") and (
        url in {"sqlite://", "sqlite:///:memory:"} or ":memory:" in url
    ):
        kwargs["connect_args"] = {"check_same_thread": False}
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


def create_schema(target_engine: Engine, metadata: MetaData) -> None:
    """Crée les tables SQLModel manquantes sur le moteur donné."""
    metadata.create_all(target_engine)


def build_db_context(database_url: str | None = None) -> AppContext:
    """Construit le moteur SQLite et la fabrique de sessions."""
    app_engine = build_engine(database_url)
    session_factory = build_session_factory(app_engine)
    return AppContext(
        engine=app_engine,
        session_factory=session_factory,
    )


def get_db_session(
    context: Annotated[AppContext, Depends(get_context)],
) -> Generator[Session, None, None]:
    """Fournit une session SQLModel liée au contexte de l'application."""
    with context.session_factory() as session:
        yield session
