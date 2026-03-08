from datetime import datetime

from pydantic import BaseModel


class UnifiedEvent(BaseModel):
    """
    Shared unified event schema used across services.
    """

    event_id: str
    sensor_id: str
    type: str
    value: float
    timestamp: datetime

