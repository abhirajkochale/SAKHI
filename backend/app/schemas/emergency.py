from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class SOSLocation(BaseModel):
    latitude: float
    longitude: float


class SOSRequest(BaseModel):
    journey_id: Optional[str] = None
    latitude: float
    longitude: float
    user_id: Optional[str] = None
    trigger_source: Literal["manual", "shake", "dead_man_switch"] = "manual"
    note: Optional[str] = None


class SOSResponse(BaseModel):
    status: str = "triggered"
    sos_id: str
    message: str
    location: SOSLocation
    journey_id: Optional[str]
    trigger_source: str
    triggered_at: datetime


class CheckinRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    user_id: Optional[str] = None


class CheckinResponse(BaseModel):
    status: str
    journey_id: str
    checked_in_at: datetime
    next_checkin_deadline: datetime
    timeout_minutes: int


class DeadManEvent(BaseModel):
    journey_id: str
    last_seen_at: datetime
    timeout_minutes: int
    location: Optional[SOSLocation] = None
    auto_sos_triggered: bool = True
