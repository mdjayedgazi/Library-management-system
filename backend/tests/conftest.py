"""Test configuration for the Library Management API."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.main import app

# Use a dedicated PostgreSQL schema for isolated tests
TEST_SCHEMA = "test_schema"


@pytest.fixture(scope="session")
async def test_engine() -> AsyncEngine:
    """Create a test database engine using a dedicated PostgreSQL schema."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Create isolated test schema and required enums
    async with engine.connect() as conn:
        await conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        await conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))
        await conn.execute(
            text(
                f"CREATE TYPE {TEST_SCHEMA}.role AS ENUM ('LIBRARIAN', 'MEMBER')"
            )
        )
        await conn.execute(
            text(
                f"CREATE TYPE {TEST_SCHEMA}.bookcategory AS ENUM ("
                f"'COMPUTER_SCIENCE', 'SCIENCE', 'HISTORY', 'BUSINESS_ECONOMICS', "
                f"'SELF_HELP', 'FICTION', 'CLASSIC_LITERATURE', 'BIOGRAPHY', "
                f"'PSYCHOLOGY', 'MATHEMATICS'"
                f")"
            )
        )
        await conn.execute(
            text(
                f"CREATE TYPE {TEST_SCHEMA}.status AS ENUM ('PENDING', 'APPROVED', 'REJECTED')"
            )
        )
        await conn.commit()

    # Create tables in the test schema
    async with engine.connect() as conn:
        await conn.execute(text(f"SET search_path TO {TEST_SCHEMA}"))
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.commit()

    yield engine

    # Cleanup: drop the entire test schema
    async with engine.connect() as conn:
        await conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        await conn.commit()
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """Create a new database session for a test using the isolated schema."""

    @event.listens_for(test_engine.sync_engine, "connect")
    def set_search_path(dbapi_conn, connection_record):
        """Set the search_path to the test schema on each new connection."""
        cursor = dbapi_conn.cursor()
        cursor.execute(f"SET search_path TO {TEST_SCHEMA}")
        cursor.close()

    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Create an async test client with overridden database dependency."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
