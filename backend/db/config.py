from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "sqlite:///./chaours.db"


class Settings(BaseSettings):
    """Configuration applicative lue depuis les variables d'environnement."""

    model_config = SettingsConfigDict(
        env_prefix="CHAOURS_",
        extra="ignore",
    )

    database_url: str = DEFAULT_DATABASE_URL


def get_settings() -> Settings:
    """Construit la configuration depuis l'environnement courant."""
    return Settings()


def resolve_database_url(database_url: str | None = None) -> str:
    """Renvoie l'URL de base demandée, sinon la configuration."""
    if database_url is not None:
        return database_url
    return get_settings().database_url
