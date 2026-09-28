"""Configuration objects, selected by ``FLASK_CONFIG`` or the factory argument."""

from __future__ import annotations

import os

from .paths import DATABASE_PATH


def _env_flag(name: str, default: bool) -> bool:
    """Read a boolean environment setting, falling back when it is absent."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str]) -> list[str]:
    """Split a comma-separated environment setting into nonempty values."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


class BaseConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DATABASE_PATH}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #: Origins allowed to call the API from a browser. ``["*"]`` is fine for a
    #: read-only demo; set CORS_ORIGINS to a comma-separated allowlist to narrow
    #: it.
    CORS_ORIGINS = _env_list("CORS_ORIGINS", ["*"])

    #: Create and populate the database at startup when it is empty.
    AUTO_SEED = _env_flag("AUTO_SEED", True)

    #: Listing pagination.
    DEFAULT_PAGE_SIZE = 12
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"  # in-memory
    AUTO_SEED = True


class ProductionConfig(BaseConfig):
    DEBUG = False


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def resolve_config(name: str | None = None) -> type[BaseConfig]:
    """Choose a config class by name or the ``FLASK_CONFIG`` setting."""
    key = (name or os.environ.get("FLASK_CONFIG") or "development").lower()
    try:
        return CONFIGS[key]
    except KeyError:
        raise ValueError(
            f"Unknown config {key!r}; expected one of {sorted(CONFIGS)}"
        ) from None
