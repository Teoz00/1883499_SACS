import logging
from typing import AsyncGenerator

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.models.rule import Base


class RuleManagementServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    service_name: str = "rule-management-service"
    host: str = "0.0.0.0"
    port: int = 8004

    database_url: PostgresDsn | str = "postgresql://postgres:postgres@postgres:5432/rules-db"


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
    Retry logic to handle PostgreSQL startup delays.
    """
    import asyncio
    
    logging.info("Initializing database...")
    logging.info(f"Using database URL: {ASYNC_DATABASE_URL}")
    
    max_retries = 5
    retry_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logging.info("Database tables created successfully")
            return
        except Exception as e:
            logging.warning(f"Database initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                logging.error("Database initialization failed after all retries")
                raise


