from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class WashroomFeedbackCreate(BaseModel):
    is_open: Optional[bool] = None
    cleanliness: Optional[str] = None
    safety: Optional[str] = None
    accessible: Optional[bool] = None

class WashroomResponse(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    is_open: Optional[bool]
    cleanliness: Optional[str]
    safety: Optional[str]
    accessible: Optional[bool]
    verified_count: int
    last_verified_timestamp: Optional[datetime]

class WashroomListResponse(BaseModel):
    washrooms: List[WashroomResponse]
