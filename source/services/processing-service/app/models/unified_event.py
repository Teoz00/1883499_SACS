from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class Metric(BaseModel):
    """A single named measurement with its value and unit."""
    name: str
    value: float
    unit: str


class UnifiedEvent(BaseModel):
    """
    Unified internal event produced by the Processing Service
    after normalizing raw simulator data.
    """
    event_id: str
    source_type: str                      # "rest" or "telemetry"
    source_id: str                        # sensor_id from raw payload
    schema_family: str                    # derived from SCHEMA_FAMILY_MAP
    timestamp: datetime                   # captured_at for REST, event_time for telemetry
    metrics: List[Metric]                 # all values, never empty
    status: Optional[str] = None         # "ok" | "warning" | None
    state_label: Optional[str] = None    # only for airlock, None for everything else
    raw: Optional[Dict[str, Any]] = None # original payload unchanged

