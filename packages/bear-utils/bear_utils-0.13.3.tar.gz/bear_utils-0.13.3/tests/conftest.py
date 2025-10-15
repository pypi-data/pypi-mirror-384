import pytest
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from bear_utils.database import DatabaseManager
from bear_utils.database.config import DatabaseConfig, sqlite_memory_db


class DummyLogger:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def info(self, msg: object, *args, **kwargs) -> None:
        self.messages.append(("info", str(msg)))

    def warning(self, msg: object, *args, **kwargs) -> None:
        self.messages.append(("warning", str(msg)))

    def success(self, msg: object, *args, **kwargs) -> None:
        self.messages.append(("success", str(msg)))

    def failure(self, msg: object, *args, **kwargs) -> None:
        self.messages.append(("failure", str(msg)))

    def error(self, msg: object, *args, **kwargs) -> None:
        self.messages.append(("error", str(msg)))

    def verbose(self, msg: object, *args, **kwargs) -> None:
        self.messages.append(("verbose", str(msg)))

    def debug(self, msg: object, *args, **kwargs) -> None:
        self.messages.append(("debug", str(msg)))


@pytest.fixture
def logger() -> DummyLogger:
    return DummyLogger()


@pytest.fixture
def default_config() -> DatabaseConfig:
    """Fixture for default database configuration."""
    return sqlite_memory_db()


MockBase = DatabaseManager.get_base()


class MockUser(MockBase):
    __tablename__ = "test_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True)


@pytest.fixture
def clean_db() -> DatabaseManager:
    """Create a clean in-memory database for testing."""
    db_manager = DatabaseManager(database_config=sqlite_memory_db())  # (tables get created automatically)
    db_manager.clear_records()
    with db_manager.open_session() as session:
        session.query(MockUser).delete()
    if not db_manager.is_registered(MockUser):
        db_manager.register_records(MockUser)
    return db_manager


@pytest.fixture
def db_with_data(clean_db: DatabaseManager) -> DatabaseManager:
    """Database with some test data."""
    with clean_db.open_session() as session:
        user1 = MockUser(name="Alice", email="alice@example.com")
        user2 = MockUser(name="Bob", email="bob@example.com")
        session.add_all([user1, user2])
    return clean_db
