from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class ContextUpdateEvent(BaseModel):
    segment_id: str
    event_type: str
    severity: float  # 0 to 100
    source: str = "simulated_demo"
    timestamp: datetime
    active: bool = True
    description: Optional[str] = None

class ContextUpdateResponse(BaseModel):
    journey_id: str
    updated_segment_id: str
    event: ContextUpdateEvent
    before: dict
    after: dict
    rerouted: bool
    reason: str
    updated_ranking: Optional[Dict[str, Any]] = None  # Re-ranked routes after recalculation
