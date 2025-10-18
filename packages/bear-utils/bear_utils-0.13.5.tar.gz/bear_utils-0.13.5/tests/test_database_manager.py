"""Tests for DatabaseManager module."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm.session import Session

from bear_dereth.models.type_fields import Password
from bear_utils.database import DatabaseManager, PostgresDB
from bear_utils.database.config import DatabaseConfig, get_default_config

from .conftest import MockUser

if TYPE_CHECKING:
    from sqlalchemy.orm.decl_api import DeclarativeMeta
    from sqlalchemy.orm.session import Session


class TestDatabaseManagerBasics:
    """Test basic DatabaseManager functionality."""

    def test_initialization_with_config(self, clean_db: DatabaseManager) -> None:
        """Test DatabaseManager initializes correctly with config."""
        assert clean_db.config.db_url.get_secret_value() == "sqlite:///:memory:"
        assert clean_db.engine is not None
        assert clean_db.SessionFactory is not None
        assert clean_db.session is not None
        assert clean_db.metadata is not None

    def test_initialization_with_defaults(self) -> None:
        """Test DatabaseManager works with default parameters."""
        db = DatabaseManager()
        assert db is not None
        assert db.config.scheme == "sqlite"

    def test_tables_created_automatically(self, clean_db: DatabaseManager) -> None:
        """Test that tables are created during initialization."""
        # Should be able to query the table without errors
        with clean_db.open_session() as session:
            count: int = session.query(MockUser).count()
            assert count == 0  # Empty but exists

    def test_postgres_subclass(self):
        """Test PostgresDB subclass uses correct defaults."""
        config = DatabaseConfig.by_schema("postgresql", name="test_db", host="testhost")
        assert PostgresDB._scheme == "postgresql"
        expected_url: str = config.db_url.get_secret_value()
        assert "postgresql://" in expected_url
        assert "testhost" in expected_url


class TestDatabaseConfiguration:
    """Test database configuration patterns and validation."""

    def test_get_default_config_sqlite(self) -> None:
        """Test get_default_config with SQLite."""
        config: DatabaseConfig = get_default_config(schema="sqlite")
        assert config.scheme == "sqlite"
        assert config.name == "database.db"
        assert "sqlite:///database.db" in config.db_url.get_secret_value()

    def test_get_default_config_postgresql(self) -> None:
        """Test get_default_config with PostgreSQL."""
        config: DatabaseConfig = get_default_config(schema="postgresql")
        assert config.scheme == "postgresql"
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.username == "postgres"
        assert config.name == "postgres"
        assert "postgresql://postgres@localhost:5432/postgres" in config.db_url.get_secret_value()

    def test_get_default_config_with_overrides(self) -> None:
        """Test get_default_config with parameter overrides."""
        config: DatabaseConfig = get_default_config(
            schema="postgresql", host="myhost", port=9999, name="mydb", user="myuser"
        )
        assert config.host == "myhost"
        assert config.port == 9999
        assert config.name == "mydb"
        assert config.username == "myuser"
        url: str = config.db_url.get_secret_value()
        assert "postgresql://myuser@myhost:9999/mydb" in url

    def test_full_config_object_creation(self) -> None:
        """Test creating full DatabaseConfig objects."""
        config = DatabaseConfig(
            scheme="postgresql",
            host="prod-db",
            port=5432,
            name="production",
            username="app_user",
            password=Password.load("secret123"),
        )

        assert config.scheme == "postgresql"
        assert config.host == "prod-db"
        assert config.username == "app_user"
        url: str = config.db_url.get_secret_value()
        assert url == "postgresql://app_user:secret123@prod-db:5432/production"

    def test_mixed_config_and_direct_params(self) -> None:
        """Test using config object with direct parameter overrides."""
        # Create base config with SQLite to avoid PostgreSQL connection
        base_config = DatabaseConfig(scheme="sqlite", name="base_db.sqlite")

        # DatabaseManager should use the config object directly
        db = DatabaseManager(database_config=base_config)
        assert db.config.scheme == "sqlite"
        assert db.config.name == "base_db.sqlite"

    def test_database_config_url_construction(self) -> None:
        """Test URL construction for different database types."""
        # SQLite with path (absolute paths get extra slash)
        sqlite_config = DatabaseConfig(scheme="sqlite", name="/path/to/db.sqlite")
        assert sqlite_config.db_url.get_secret_value() == "sqlite:////path/to/db.sqlite"

        # PostgreSQL with all components
        pg_config = DatabaseConfig(
            scheme="postgresql",
            host="db.example.com",
            port=5432,
            name="myapp",
            username="user",
            password=Password.load("pass"),
        )
        assert pg_config.db_url.get_secret_value() == "postgresql://user:pass@db.example.com:5432/myapp"

        # MySQL
        mysql_config = DatabaseConfig(
            scheme="mysql",
            host="mysql-server",
            port=3306,
            name="webapp",
            username="root",
        )
        assert mysql_config.db_url.get_secret_value() == "mysql://root@mysql-server:3306/webapp"

    def test_database_config_defaults_by_scheme(self) -> None:
        """Test that schemes set appropriate defaults."""
        # PostgreSQL defaults
        pg_config: DatabaseConfig = DatabaseConfig.by_schema(scheme="postgresql")
        assert pg_config.host == "localhost"
        assert pg_config.port == 5432
        assert pg_config.username == "postgres"
        assert pg_config.name == "postgres"

        # MySQL defaults
        mysql_config: DatabaseConfig = DatabaseConfig.by_schema(scheme="mysql")
        assert mysql_config.host == "localhost"
        assert mysql_config.port == 3306
        assert mysql_config.username == "root"
        assert mysql_config.name == "mysql"

        # SQLite defaults
        sqlite_config: DatabaseConfig = DatabaseConfig.by_schema(scheme="sqlite")
        assert sqlite_config.host is None
        assert sqlite_config.port is None
        assert sqlite_config.username is None
        assert sqlite_config.name == "database.db"

    def test_database_manager_with_different_configs(self) -> None:
        """Test DatabaseManager with various configuration patterns."""
        config1: DatabaseConfig = get_default_config(schema="sqlite", name=":memory:")
        db1 = DatabaseManager(database_config=config1)
        assert ":memory:" in db1.config.db_url.get_secret_value()

        config2 = DatabaseConfig(scheme="sqlite", name="test.db")
        db2 = DatabaseManager(database_config=config2)
        assert "test.db" in db2.config.db_url.get_secret_value()

        # Test with no config (defaults)
        db3 = DatabaseManager()
        assert db3.config.scheme == "sqlite"

        # clean up the databases if they were created on disk

        if Path("test.db").exists():
            Path("test.db").unlink()
        if Path("database.db").exists():
            Path("database.db").unlink()
        if Path("base_db.sqlite").exists():
            Path("base_db.sqlite").unlink()
        if Path("mydb").exists():
            Path("mydb").unlink()


class TestDatabaseManagerOperations:
    """Test DatabaseManager helper operations."""

    def test_get_all_records_empty(self, clean_db: DatabaseManager):
        """Test getting all records from empty table."""
        users: list[MockUser] = clean_db.get(MockUser)
        assert users == []

    def test_get_all_records_with_data(self, db_with_data: DatabaseManager) -> None:
        """Test getting all records with data."""
        users: list[MockUser] = db_with_data.get(MockUser)
        assert len(users) == 2
        names: list[str] = [user.name for user in users]
        assert "Alice" in names
        assert "Bob" in names

    def test_count_records_empty(self, clean_db: DatabaseManager) -> None:
        """Test counting records in empty table."""
        count: int = clean_db.count("MockUser")
        assert count == 0

    def test_count_records_with_data(self, db_with_data: DatabaseManager) -> None:
        """Test counting records with data."""
        count: int = db_with_data.count(MockUser)
        assert count == 2

    def test_get_records_by_var(self, db_with_data: DatabaseManager) -> None:
        """Test getting records by variable."""
        users: list[MockUser] = db_with_data.get(MockUser, name="Alice")
        assert len(users) == 1
        alice: MockUser = users[0]
        assert alice.name == "Alice"
        assert alice.email == "alice@example.com"

    def test_get_records_by_var_no_match(self, db_with_data: DatabaseManager) -> None:
        """Test getting records with no match."""
        users: int = db_with_data.count(MockUser, name="Charlie")
        assert users == 0

    def test_count_records_by_var(self, db_with_data: DatabaseManager) -> None:
        """Test counting records by variable."""
        count: int = db_with_data.count(MockUser, name="Alice")
        assert count == 1

        count = db_with_data.count(MockUser, name="NonExistent")
        assert count == 0


class TestSessionManagement:
    """Test session management functionality."""

    def test_open_session_context_manager(self, clean_db: DatabaseManager) -> None:
        """Test the open_session context manager."""
        with clean_db.open_session() as session:
            user = MockUser(name="Test", email="test@example.com")
            session.add(user)
        users: list[MockUser] = clean_db.get(MockUser)
        assert len(users) == 1
        assert users[0].name == "Test"

    def test_get_session_manual(self, clean_db: DatabaseManager) -> None:
        """Test manual session management."""
        session: Session = clean_db.get_session()
        assert session is not None
        user = MockUser(name="Manual", email="manual@test.com")
        session.add(user)
        session.commit()
        session.close()
        count: int = clean_db.count(MockUser)
        assert count == 1


class TestBaseClassManagement:
    """Test base class management system."""

    def test_get_base_creates_default(self) -> None:
        """Test that get_base creates a default when none exists."""
        base: DeclarativeMeta = DatabaseManager.get_base()
        assert base is not None
        assert hasattr(base, "metadata")

    def test_set_and_get_base(self) -> None:
        """Test setting and retrieving custom base."""
        custom_base = declarative_base()
        DatabaseManager.set_base(custom_base)
        retrieved_base: DeclarativeMeta = DatabaseManager.get_base()

        assert retrieved_base is custom_base

    def test_clear_bases(self) -> None:
        """Test clearing base classes."""
        base: DeclarativeMeta = DatabaseManager.get_base()
        assert base is not None


class TestIntegration:
    """Integration tests for real-world usage patterns."""

    def test_basic_crud_workflow(self, clean_db: DatabaseManager) -> None:
        """Test a basic CRUD workflow."""
        # CREATE
        with clean_db.open_session() as session:
            user = MockUser(name="CRUD", email="crud@test.com")
            session.add(user)

        # READ
        users: list[MockUser] = clean_db.get(MockUser, name="CRUD")
        assert len(users) == 1
        user_id: int = users[0].id

        # UPDATE
        with clean_db.open_session() as session:
            user: MockUser | None = session.get(MockUser, user_id)
            assert user is not None
            user.email = "updated@test.com"

        # Verify update
        updated_users: list[MockUser] = clean_db.get(MockUser, email="updated@test.com")
        assert len(updated_users) == 1
        assert updated_users[0].name == "CRUD"

        # # DELETE
        session: Session = clean_db.get_session()
        session.delete(session.get(MockUser, user_id))
        session.commit()

        final_count: int = clean_db.count(MockUser)
        assert final_count == 0

    def test_error_recovery(self, db_with_data: DatabaseManager) -> None:
        """Test that database recovers from errors."""
        # Try to create duplicate email (should fail)

        with pytest.raises(IntegrityError), db_with_data.open_session() as session:  # noqa: PT012
            duplicate_user = MockUser(name="Duplicate", email="alice@example.com")
            session.add(duplicate_user)
            session.flush()

        count: int = db_with_data.count(MockUser)
        assert count == 2  # Original data still there

        # Should be able to add valid data
        with db_with_data.open_session() as session:
            valid_user = MockUser(name="Valid", email="valid@test.com")
            session.add(valid_user)

        final_count: int = db_with_data.count(MockUser)
        assert final_count == 3
