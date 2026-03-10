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
    on-demand for immediate rule evaluation.
    """

    def __init__(
        self,
        database_url: str,
    ) -> None:
        self._database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None

    async def start(self) -> None:
        """
        Initialize the connection pool.
        Rules are loaded on-demand during get_rules() calls.
        """
        if self._pool is not None:
            return

        logger.info("Creating asyncpg connection pool for rules repository.")

        delay = 1.0
        while True:
            try:
                self._pool = await asyncpg.create_pool(dsn=self._database_url)
                break
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to initialize rules repository (will retry in %.1fs): %s",
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30.0)

    async def stop(self) -> None:
        """
        Close the connection pool.
        """
        if self._pool is not None:
            logger.info("Closing asyncpg connection pool for rules repository.")
            await self._pool.close()
            self._pool = None

    async def get_rules(self) -> List[Rule]:
        """
        Load and return the latest enabled rules from the database.
        This ensures newly created/enabled rules are available immediately.
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

        logger.info("Loaded %d enabled rules from database.", len(rules))
        return rules

