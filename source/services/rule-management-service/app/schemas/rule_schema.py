from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RuleBase(BaseModel):
    """
    Rule schema. The rule engine requires the FULL DSL in 'condition':
    "IF <sensor> <op> <value> [unit] THEN set <actuator> to ON|OFF"
    Example: "IF greenhouse_temperature > 28 °C THEN set cooling_fan to ON"
    'action' can store the extracted action for display (e.g. "set cooling_fan to ON").
    """
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
    # Pydantic v2: enable reading from ORM objects when using from_orm.
    model_config = ConfigDict(from_attributes=True)

