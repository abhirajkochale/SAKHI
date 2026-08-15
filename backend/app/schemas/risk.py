from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class SegmentContext(BaseModel):
    """
    Raw contextual data available for a specific JourneySegment.
    """
    departure_time: Optional[datetime] = None
    footfall_indicator: Optional[float] = None
    cctv_coverage: Optional[float] = None
    police_proximity: Optional[float] = None
    transit_access: Optional[float] = None
    infrastructure_score: Optional[float] = None
    historical_baseline: Optional[float] = None
    validated_report_signal: Optional[float] = None
    weather_context: Optional[str] = None
    event_context: Optional[str] = None

class RiskFeatures(BaseModel):
    """
    Normalized feature vector extracted from the context.
    Values are typically 0.0 to 1.0.
    """
    hour_sin: float
    hour_cos: float
    is_weekend: float
    environmental_isolation_indicator: float
    cctv_coverage: float
    police_proximity: float
    transit_access: float
    infrastructure_score: float
    historical_baseline: float
    validated_report_signal: float

class SHAPContribution(BaseModel):
    feature_name: str
    feature_value: float
    shap_value: float
    direction: str  # "increases_risk" or "decreases_risk"

class RiskExplanation(BaseModel):
    available: bool
    base_value: Optional[float] = None
    predicted_risk: Optional[float] = None
    top_positive_factors: Optional[List[SHAPContribution]] = None
    top_negative_factors: Optional[List[SHAPContribution]] = None
    all_contributions: Optional[List[SHAPContribution]] = None
    reason: Optional[str] = None

class RiskScore(BaseModel):
    """
    The calculated contextual safety risk score for a segment.
    """
    segment_id: str
    risk_score: float  # 0 to 100
    confidence_score: float  # 0 to 100
    confidence_level: str  # HIGH, MEDIUM, LOW, Insufficient Data
    model_source: str  # "xgboost" or "heuristic"
    model_version: str  # e.g., "0.1.0" or "prototype"
    explanation: Optional[RiskExplanation] = None
    factors: Dict[str, float]
    generated_at: datetime
