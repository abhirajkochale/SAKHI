from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class Location(BaseModel):
    latitude: float
    longitude: float

class JourneyRequest(BaseModel):
    origin: Location
    destination: Location
    departure_time: Optional[datetime] = None

class JourneySegment(BaseModel):
    segment_id: str
    journey_id: str
    sequence: int
    mode: str = "walking"
    start_location: Location
    end_location: Location
    distance_m: float
    duration_s: float
    geometry: Dict[str, Any]  # GeoJSON LineString

class JourneyResponse(BaseModel):
    journey_id: str
    origin: Location
    destination: Location
    distance_m: float
    duration_s: float
    segments: List[JourneySegment]
