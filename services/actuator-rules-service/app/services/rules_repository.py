import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional

import asyncpg


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Rule:
    """
    In-memory representation of a rule row.
    """

    id: str
    name: str
    condition: str
    action: str
    enabled: bool


class RulesRepository:
    """
    Repository responsible for loading enabled rules from PostgreSQL
    and periodically refreshing them into an in-memory cache.
    """

    def __init__(
        self,
        database_url: str,
        refresh_interval_seconds: float = 10.0,
    ) -> None:
        self._database_url = database_url
        self._refresh_interval = refresh_interval_seconds

        self._pool: Optional[asyncpg.Pool] = None
        self._rules: List[Rule] = []
        self._refresh_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """
        Initialize the connection pool, perform an initial load,
        and start the periodic refresh task.
        """
        if self._pool is not None:
            return

        logger.info("Creating asyncpg connection pool for rules repository.")

        delay = 1.0
        while True:
            try:
                self._pool = await asyncpg.create_pool(dsn=self._database_url)
                await self._load_rules()
                break
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to initialize rules repository (will retry in %.1fs): %s",
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30.0)

        loop = asyncio.get_event_loop()
        self._refresh_task = loop.create_task(self._refresh_loop(), name="rules-refresh")

    async def stop(self) -> None:
        """
        Stop the periodic refresh task and close the connection pool.
        """
        if self._refresh_task is not None:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                logger.info("Rules refresh task cancelled.")
            finally:
                self._refresh_task = None

        if self._pool is not None:
            logger.info("Closing asyncpg connection pool for rules repository.")
            await self._pool.close()
            self._pool = None

    async def _refresh_loop(self) -> None:
        """
        Background loop that periodically reloads enabled rules.
        """
        logger.info(
            "Starting rules refresh loop with interval=%ss", self._refresh_interval
        )
        try:
            while True:
                await asyncio.sleep(self._refresh_interval)
                try:
                    await self._load_rules()
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error("Failed to refresh rules from database: %s", exc)
        except asyncio.CancelledError:
            logger.info("Rules refresh loop cancelled.")
            raise

    async def _load_rules(self) -> None:
        """
        Load all enabled rules from the database into the local cache.
        """
        if self._pool is None:
            raise RuntimeError("RulesRepository not started; connection pool is None.")

        query = """
            SELECT id, name, condition, action, enabled
            FROM rules
            WHERE enabled = TRUE
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query)

        rules = [
            Rule(
                id=str(row["id"]),
                name=row["name"],
                condition=row["condition"],
                action=row["action"],
                enabled=row["enabled"],
            )
            for row in rows
        ]

        async with self._lock:
            self._rules = rules

        logger.info("Loaded %d enabled rules from database.", len(rules))

    async def get_rules(self) -> List[Rule]:
        """
        Return a snapshot list of the currently cached rules.
        """
        async with self._lock:
            return list(self._rules)

