from db.config import DEFAULT_DATABASE_URL, Settings, resolve_database_url


def test_settings_use_default_database_url(monkeypatch):
    monkeypatch.delenv("CHAOURS_DATABASE_URL", raising=False)

    assert Settings().database_url == DEFAULT_DATABASE_URL


def test_settings_read_database_url_from_environment(monkeypatch):
    monkeypatch.setenv("CHAOURS_DATABASE_URL", "sqlite:///./environment.db")

    assert Settings().database_url == "sqlite:///./environment.db"


def test_resolve_database_url_prefers_explicit_argument(monkeypatch):
    monkeypatch.setenv("CHAOURS_DATABASE_URL", "sqlite:///./environment.db")

    assert resolve_database_url("sqlite://") == "sqlite://"
