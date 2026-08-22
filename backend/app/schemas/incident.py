from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class IncidentCreate(BaseModel):
    segment_id: str
    event_type: str
    severity: float = Field(..., ge=0.0, le=100.0)
    latitude: float
    longitude: float
    description: Optional[str] = None

class IncidentResponse(BaseModel):
    id: int
    segment_id: str
    event_type: str
    severity: float
    latitude: float
    longitude: float
    timestamp: datetime
    active: int
    description: Optional[str]

    class Config:
        orm_mode = True
