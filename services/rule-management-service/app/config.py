from typing import AsyncGenerator

from pydantic import BaseSettings, PostgresDsn
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.models.rule import Base


class RuleManagementServiceSettings(BaseSettings):
    service_name: str = "rule-management-service"
    host: str = "0.0.0.0"
    port: int = 8004

    database_url: PostgresDsn | str = "postgresql://postgres:postgres@postgres:5432/rules-db"

    class Config:
        env_file = ".env"


settings = RuleManagementServiceSettings()


def _make_async_database_url(url: str) -> str:
    """
    Convert a standard PostgreSQL URL into an asyncpg SQLAlchemy URL.
    """
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    return url


ASYNC_DATABASE_URL = _make_async_database_url(str(settings.database_url))

engine: AsyncEngine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """
    Initialize the database by creating tables if they do not exist.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


