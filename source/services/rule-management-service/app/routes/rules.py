from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_session
from app.schemas.rule_schema import RuleCreate, RuleRead, RuleUpdate
from app.services import rule_service


router = APIRouter(prefix="/rules", tags=["rules"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=RuleRead,
    summary="Create rule",
)
async def create_rule_endpoint(
    payload: RuleCreate,
    session: AsyncSession = Depends(get_session),
) -> RuleRead:
    rule = await rule_service.create_rule(session, payload)
    return RuleRead.from_orm(rule)


@router.get(
    "/",
    response_model=List[RuleRead],
    summary="List all rules",
)
async def list_rules_endpoint(
    session: AsyncSession = Depends(get_session),
) -> List[RuleRead]:
    rules = await rule_service.list_rules(session)
    return [RuleRead.from_orm(r) for r in rules]


@router.get(
    "/{rule_id}",
    response_model=RuleRead,
    summary="Get rule by ID",
)
async def get_rule_endpoint(
    rule_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> RuleRead:
    rule = await rule_service.get_rule(session, rule_id)
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    return RuleRead.from_orm(rule)


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete rule",
)
async def delete_rule_endpoint(
    rule_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    deleted = await rule_service.delete_rule(session, rule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )


@router.put(
    "/{rule_id}",
    response_model=RuleRead,
    summary="Update rule",
)
async def update_rule_endpoint(
    rule_id: UUID,
    payload: RuleUpdate,
    session: AsyncSession = Depends(get_session),
) -> RuleRead:
    rule = await rule_service.update_rule(session, rule_id, payload)
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    return RuleRead.from_orm(rule)


