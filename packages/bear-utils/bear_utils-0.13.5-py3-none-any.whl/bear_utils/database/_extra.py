from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import DeclarativeMeta, Query, QueryableAttribute, scoped_session


class DynamicRecords[T]:
    """A simple class to hold records of a specific type."""

    def __init__(self, tbl_obj: type[T], session: scoped_session) -> None:
        """Initialize the RecordsHolder with a table object and session."""
        self.tbl_obj: type[T] = tbl_obj
        self.session: scoped_session = session

    def __len__(self) -> int:
        """Get the number of records of the specified type."""
        return self.query().count()

    def count(self) -> int:
        """Get the number of records of the specified type."""
        return len(self)

    def query(self) -> Query[T]:
        """Query all records of the specified type."""
        return self.session.query(self.tbl_obj)

    def all(self) -> list[T]:
        """Get all records of the specified type."""
        return self.query().all()

    def search(self, search: str, *columns: QueryableAttribute) -> list[T]:
        """Search records by specified columns."""
        if not columns:
            raise ValueError("At least one column must be specified for search.")
        query: Query[T] = self.query()
        search_pattern: str = f"%{search}%"
        filters: list = [column.ilike(search_pattern) for column in columns]
        return query.filter(*filters).all()

    def filter_by(self, **kwargs: Any) -> list[T]:
        """Filter records by specified keyword arguments."""
        return self.query().filter_by(**kwargs).all()

    def first(self) -> T | None:
        """Get the first record of the specified type."""
        return self.query().first()

    def get(self, ident: Any) -> T | None:
        """Get a record by its primary key."""
        return self.session.get(entity=self.tbl_obj, ident=ident)

    def add(self, instance: T) -> None:
        """Add a new record to the session."""
        self.session.add(instance)

    def delete(self, instance: T) -> None:
        """Delete a record from the session."""
        self.session.delete(instance)

    def commit(self) -> None:
        """Commit the current transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.session.rollback()

    def refresh(self, instance: T) -> None:
        """Refresh the instance with the latest data from the database."""
        self.session.refresh(instance)


def attr_name(cls: str, attr: str = "data") -> str:
    """Generate a standardized attribute name for storing per-class data.

    Args:
        cls (str): The class name.
        attr (str): The attribute name.

    Returns:
        str: The standardized attribute name.
    """
    return f"_{cls}_{attr}"


@dataclass(slots=True)
class PerClassData:
    """Data class to hold per-class database information."""

    base: DeclarativeMeta | None = None
    scoped_sess: scoped_session | None = None


class DatabaseManagerMeta(type):
    def __new__(mcs, name: str, bases: tuple, namespace: dict, bypass: bool = True) -> Any:
        if not bases and bypass:
            return super().__new__(mcs, name, bases, namespace)
        container_name: str = attr_name(name)
        namespace[container_name] = PerClassData()
        return super().__new__(mcs, name, bases, namespace)

    @property
    def _name(cls) -> str:
        """Get the name of the class."""
        return cls.__name__

    @property
    def _meta_name(cls) -> str:
        return attr_name(cls.__name__)

    @property
    def _internal(cls) -> PerClassData:
        """Get the internal data attribute name for the class."""
        if not hasattr(cls, cls._meta_name):
            raise AttributeError(f"Class {cls._name} is missing internal data attribute {cls._meta_name}")
        return getattr(cls, cls._meta_name)

    @property
    def _base(cls) -> DeclarativeMeta | None:
        """Get the base class for the database manager."""
        return cls._internal.base

    def _set_base(cls, value: DeclarativeMeta | None) -> None:
        """Set the base class for the database manager."""
        cls._internal.base = value

    def _get_base(cls) -> DeclarativeMeta:
        """Get the base class for the database manager, creating it if necessary."""
        return cls._base  # type: ignore[return-value]

    @property
    def _scoped_session(cls) -> scoped_session | None:
        """Get the scoped session for the database manager."""
        return cls._internal.scoped_sess

    @_scoped_session.setter
    def _scoped_session(cls, value: scoped_session | None) -> None:
        """Set the scoped session for the database manager."""
        cls._internal.scoped_sess = value
