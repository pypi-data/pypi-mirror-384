"""Database Manager Module for managing database connections and operations."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, ClassVar, Literal, overload
from warnings import deprecated

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeMeta, declarative_base, scoped_session, sessionmaker

from bear_utils.database._extra import DatabaseManagerMeta, DynamicRecords
from bear_utils.database.config import DatabaseConfig, Schemas, get_default_config

if TYPE_CHECKING:
    from collections.abc import Generator

    from pydantic import SecretStr
    from sqlalchemy.orm.session import Session


def get_name(obj: str | type) -> str:
    """Get the name of a class or return the string if already a string.

    Args:
        obj (str | type): The class or string to get the name from.

    Returns:
        str: The name of the class or the string itself.
    """
    if isinstance(obj, str):
        return obj
    return obj.__name__


class DatabaseManager(metaclass=DatabaseManagerMeta, bypass=False):
    """A class to manage database connections and operations."""

    _scheme: ClassVar[Schemas] = "sqlite"

    @classmethod
    def set_base(cls, base: DeclarativeMeta | None) -> None:
        """Set the base class for this database class."""
        cls._set_base(base)

    @classmethod
    def get_base(cls) -> DeclarativeMeta:
        """Get the base class for this database class."""
        if cls._base is None:
            cls._set_base(declarative_base())
        return cls._get_base()

    @classmethod
    def clear_base(cls) -> None:
        """Clear the base class for this database class."""
        cls._set_base(None)

    @classmethod
    def set_scheme(cls, scheme: Schemas) -> None:
        """Set the default scheme for the database manager."""
        cls._scheme = scheme

    def __init__(
        self,
        database_config: DatabaseConfig | None = None,
        host: str = "",
        port: int = 0,
        user: str = "",
        password: str | SecretStr = "",
        name: str = "",
        schema: Schemas | None = None,
    ) -> None:
        """Initialize the DatabaseManager with a database URL or connection parameters."""
        self.config: DatabaseConfig = database_config or get_default_config(
            schema=schema or self._scheme,
            host=host,
            port=port,
            name=name,
            user=user,
            password=password,
        )
        self.dynamic_records: dict[str, DynamicRecords] = {}
        self.engine: Engine = create_engine(self.config.db_url.get_secret_value(), echo=False)
        self.metadata: MetaData = self.get_base().metadata
        self.SessionFactory: sessionmaker[Session] = sessionmaker(bind=self.engine)
        if self.instance_session is None:
            self.set_session(scoped_session(self.SessionFactory))
        self.session: scoped_session[Session] = self.get_session(scoped=True)
        self.create_tables()

    def register_records[T_Table](self, tbl_obj: type[T_Table], name: str | None = None) -> DynamicRecords[T_Table]:
        """Register a table class for dynamic record access.

        Args:
            name (str): The name to register the table class under.
            tbl_obj (type[T]): The table class to register.

        Returns:
            DynamicRecords[T]: An instance of DynamicRecords for the table class.
        """
        name = get_name(tbl_obj) if name is None else name

        if name in self.dynamic_records:
            raise ValueError(f"Records for {name} are already registered.")
        records: DynamicRecords[T_Table] = DynamicRecords(tbl_obj=tbl_obj, session=self.session)
        self.dynamic_records[name] = records
        return records

    def is_registered(self, name: str | type) -> bool:
        """Check if a table class is registered.

        Args:
            name (str | type): The name of the registered table class or the class itself.

        Returns:
            bool: True if the table class is registered, False otherwise.
        """
        return get_name(name) in self.dynamic_records

    def clear_records(self) -> None:
        """Clear all registered dynamic records."""
        self.dynamic_records.clear()

    def get_all[T_Table](self, name: str | type[T_Table]) -> list[T_Table]:  # type: ignore[override]
        """Get all records from a table.

        Args:
            name (str): The name of the registered table class.

        Returns:
            list[T_Table]: A list of all records in the table.
        """
        name = get_name(name)
        if name not in self.dynamic_records:
            raise ValueError(f"Records for {name} are not registered.")
        records: DynamicRecords[T_Table] = self.dynamic_records[name]
        return records.all()

    def count[T_Table](self, o: str | type[T_Table], **kwargs) -> int:
        """Count the number of records in a table.

        Args:
            name (str): The name of the registered table class.

        Returns:
            int: The count of records in the table.
        """
        name: str = get_name(o)
        if name not in self.dynamic_records:
            raise ValueError(f"Records for {name} are not registered.")
        records: DynamicRecords[T_Table] = self.dynamic_records[name]
        return records.count() if not kwargs else len(records.filter_by(**kwargs))

    def get[T_Table](self, o: str | type[T_Table], **kwargs) -> list[T_Table]:  # type: ignore[override]
        """Get records from a table by a specific variable.

        Args:
            name (str): The name of the registered table class.
            **kwargs: The variable/column name and value to filter by.

        Returns:
            list[T_Table]: A list of records matching the filter.
        """
        name: str = get_name(o)
        if name not in self.dynamic_records:
            raise ValueError(f"Records for {name} are not registered.")
        records: DynamicRecords[T_Table] = self.dynamic_records[name]
        return records.filter_by(**kwargs)

    @property
    def instance_session(self) -> scoped_session | None:
        """Get the scoped session for this database class."""
        return self.__class__._scoped_session

    @instance_session.setter
    def instance_session(self, value: scoped_session | None) -> None:
        self.__class__._scoped_session = value

    @overload
    def get_session(self, scoped: Literal[True]) -> scoped_session: ...

    @overload
    def get_session(self, scoped: Literal[False] = False) -> Session: ...

    def get_session(self, scoped: bool = False) -> scoped_session | Session:
        """Get the scoped session for this database class.

        Args:
            scoped (bool): Whether to return a scoped session or a regular session.

        Returns:
            scoped_session | Session: The scoped session or regular session.
        """
        if self.instance_session is None:
            self.instance_session = scoped_session(self.SessionFactory)
        return self.instance_session if scoped else self.instance_session()

    def set_session(self, session: scoped_session) -> None:
        """Set the scoped session for this database class."""
        self.instance_session = session

    @contextmanager
    def open_session(self) -> Generator[Session, Any]:
        """Provide a transactional scope around a series of operations."""
        session: Session = self.session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    def close_session(self) -> None:
        """Close the session."""
        if self.instance_session is not None:
            self.session.remove()
        self.instance_session = None

    def create_tables(self) -> None:
        """Create all tables defined by Base"""
        self.metadata.create_all(self.engine)

    def debug_tables(self) -> dict[str, Any]:
        """Get the tables defined in the metadata."""
        base: DeclarativeMeta = self.get_base()
        return base.metadata.tables

    def close(self) -> None:  # Changing to use this method name since it's more intuitive and standard.
        """Close the session and connection."""
        self.close_session()
        if self.engine is not None:
            self.engine.dispose()
            self.engine = None  # type: ignore[assignment]

    @deprecated("Use close() instead, this method will be removed in a future version.")
    def close_all(self) -> None:
        """Close all sessions and connections."""
        self.close()


class SqliteDB(DatabaseManager):
    """SQLite Database Manager, inherits from DatabaseManager and sets the scheme to sqlite."""

    _scheme: ClassVar[Schemas] = "sqlite"


class PostgresDB(DatabaseManager):
    """Postgres Database Manager, inherits from DatabaseManager and sets the scheme to postgresql."""

    _scheme: ClassVar[Schemas] = "postgresql"


class MySQLDB(DatabaseManager):
    """MySQL Database Manager, inherits from DatabaseManager and sets the scheme to mysql."""

    _scheme: ClassVar[Schemas] = "mysql"


# NOTE: Instead of using a SingletonDB directly, you can import SingletonWrap and wrap any of the above classes.
#
# Example:
# from singleton_base import SingletonWrap
# from bear_utils.database import PostgresDB
# PostgresSingleton = SingletonWrap(PostgresDB, host='localhost', user='user', password='pass', name='dbname')
# db_instance = PostgresSingleton.get()


__all__ = ["DatabaseManager", "MySQLDB", "PostgresDB", "SqliteDB"]
