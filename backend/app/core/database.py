from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session() as db:
        yield db


db_Dependency = Annotated[
    AsyncSession,
    Depends(get_db),
]


def create_tables(connection: Connection) -> None:
    SQLModel.metadata.create_all(bind=connection)


async def create_db_and_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(create_tables)
