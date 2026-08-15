from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from app.schemas.journey import JourneySegment

class RouteMetrics(BaseModel):
    total_distance_m: float
    total_duration_s: float
    route_risk_score: float
    max_segment_risk: float
    min_confidence: float
    average_confidence: float
    uncertainty_penalty: float

class RouteCandidate(BaseModel):
    route_id: str
    metrics: RouteMetrics
    segments: List[JourneySegment]

class RouteOption(BaseModel):
    route_id: str
    mode: str
    rank: int
    distance_m: float
    duration_s: float
    risk_score: float
    confidence: float
    max_segment_risk: float
    uncertainty_penalty: float
    route_cost: float
    segments: List[JourneySegment]

class RouteRankingResponse(BaseModel):
    journey_id: str
    safest_route: Optional[RouteOption] = None
    balanced_route: Optional[RouteOption] = None
    fastest_route: Optional[RouteOption] = None
    all_candidates: List[RouteCandidate]
