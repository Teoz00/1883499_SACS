from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class ActuatorCommand(BaseModel):
    """
    Outgoing command to be published to the `actuator-commands` topic.
    """

    actuator_id: str
    command: Literal["ON", "OFF"]
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

