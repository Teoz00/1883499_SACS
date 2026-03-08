from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RuleBase(BaseModel):
    name: str
    condition: str
    action: str
    enabled: bool = True


class RuleCreate(RuleBase):
    """
    Schema for creating a new rule.
    """


class RuleUpdate(RuleBase):
    """
    Schema for updating an existing rule.
    """


class RuleRead(RuleBase):
    """
    Schema returned in responses.
    """

    id: UUID

    class Config:
        orm_mode = True

