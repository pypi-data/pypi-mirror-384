"""Database configuration utilities."""

from pydantic import SecretStr

from bear_dereth.models.type_fields import Password
from bear_utils.database.schemas import DatabaseConfig, DBConfig, Schemas, get_defaults


def get_default_config(
    schema: Schemas,
    host: str | None = None,
    port: int | None = None,
    name: str | None = None,
    user: str | None = None,
    password: str | SecretStr | None = None,
) -> DatabaseConfig:
    """Get the default database configuration for a given scheme."""
    defaults: DBConfig = get_defaults(schema)
    return DatabaseConfig(
        scheme=schema,
        host=host or defaults.host,
        port=port or defaults.port,
        name=name or defaults.name,
        username=user or defaults.username,
        password=Password.load(password) if password else None,
    )


def sqlite_memory_db() -> DatabaseConfig:
    """Get a SQLite in-memory database configuration."""
    return DatabaseConfig(scheme="sqlite", name=":memory:")


def sqlite_default_db() -> DatabaseConfig:
    """Get a SQLite default database configuration."""
    return get_default_config(schema="sqlite")


def mysql_default_db() -> DatabaseConfig:
    """Get a MySQL default database configuration."""
    return get_default_config(schema="mysql")


def postgres_default_db() -> DatabaseConfig:
    """Get a PostgreSQL default database configuration."""
    return get_default_config(schema="postgresql")


__all__ = [
    "get_default_config",
    "mysql_default_db",
    "postgres_default_db",
    "sqlite_default_db",
    "sqlite_memory_db",
]
