import logging
from typing import Mapping, Any
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from app.models.unified_event import UnifiedEvent

logger = logging.getLogger(__name__)


class RawEvent(BaseModel):
    sensor_id: str
    type: str
    value: float
    timestamp: str


def transform_raw_event(raw: Mapping[str, Any]) -> UnifiedEvent:
    """
    Validate an incoming raw event payload and convert it into a UnifiedEvent.
    """
    try:
        raw_event = RawEvent.parse_obj(raw)
    except ValidationError as exc:
        logger.error("Invalid raw event payload: %s", exc)
        raise

    unified = UnifiedEvent(
        event_id=str(uuid4()),
        sensor_id=raw_event.sensor_id,
        type=raw_event.type,
        value=raw_event.value,
        timestamp=raw_event.timestamp,
    )
    logger.debug(
        "Transformed raw event sensor_id=%s into UnifiedEvent event_id=%s",
        unified.sensor_id,
        unified.event_id,
    )
    return unified

