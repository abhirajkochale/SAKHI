from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WashroomFeedbackCreate(BaseModel):
    is_open: bool
    cleanliness: str
    safety: str
    accessible: bool

class WashroomResponse(BaseModel):
    id: int
    name: str
    address: Optional[str]
    latitude: float
    longitude: float
    
    # Aggregated fields
    is_open: bool
    cleanliness: str
    safety: str
    accessible: bool
    verified_count: int
    last_verified_timestamp: Optional[datetime]

    class Config:
        from_attributes = True
