from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule
from app.schemas.rule_schema import RuleCreate, RuleUpdate


async def create_rule(session: AsyncSession, data: RuleCreate) -> Rule:
    rule = Rule(
        name=data.name,
        condition=data.condition,
        action=data.action,
        enabled=data.enabled,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def list_rules(session: AsyncSession) -> List[Rule]:
    result = await session.execute(select(Rule).order_by(Rule.name))
    return list(result.scalars().all())


async def get_rule(session: AsyncSession, rule_id: UUID) -> Optional[Rule]:
    result = await session.execute(select(Rule).where(Rule.id == rule_id))
    return result.scalar_one_or_none()


async def delete_rule(session: AsyncSession, rule_id: UUID) -> bool:
    """
    Delete a rule. Returns True if a row was deleted, False otherwise.
    """
    result = await session.execute(
        delete(Rule).where(Rule.id == rule_id).returning(Rule.id)
    )
    deleted = result.scalar_one_or_none()
    await session.commit()
    return deleted is not None


async def update_rule(
    session: AsyncSession,
    rule_id: UUID,
    data: RuleUpdate,
) -> Optional[Rule]:
    rule = await get_rule(session, rule_id)
    if rule is None:
        return None

    rule.name = data.name
    rule.condition = data.condition
    rule.action = data.action
    rule.enabled = data.enabled

    await session.commit()
    await session.refresh(rule)
    return rule

