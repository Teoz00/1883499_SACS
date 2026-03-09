from datetime import datetime

from pydantic import BaseModel


class UnifiedEvent(BaseModel):
    """
    Unified event schema used by the actuator-rules-service.
    Matches the shared unified event schema.
    """

    event_id: str
    sensor_id: str
    type: str
    value: float
    timestamp: datetime
    status: str | None = None

