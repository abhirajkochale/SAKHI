from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class SegmentContext(BaseModel):
    """
    Raw contextual data available for a specific JourneySegment.
    Populated from spatial lookup + temporal derivation + optional overrides.
    """
    departure_time: Optional[datetime] = None

    # Rich spatial context (populated by SegmentLookupService)
    segment_lat: Optional[float] = None
    segment_lon: Optional[float] = None
    district: Optional[str] = None

    # Historical district context (real NCRB data - district level only)
    historical_baseline: Optional[float] = None        # 0-100 normalized
    cases_per_100k: Optional[float] = None
    severity_weighted_cases_per_100k: Optional[float] = None
    recent_cases_per_100k: Optional[float] = None
    recent_severity_per_100k: Optional[float] = None
    crime_trend_slope: Optional[float] = None

    # Road characteristics (from OSM/OSRM)
    distance_m: Optional[float] = None
    estimated_travel_time_s: Optional[float] = None

    # Environmental context (synthetic/proxy - clearly labelled)
    lighting_score: Optional[float] = None            # synthetic proxy 0-100
    cctv_coverage_score: Optional[float] = None       # synthetic proxy 0-100
    footfall_proxy: Optional[float] = None            # synthetic proxy
    contextual_footfall_proxy: Optional[float] = None # synthetic proxy, time-adjusted

    # Infrastructure distances (real GPS-computed from real facility coordinates)
    distance_to_police_m: Optional[float] = None
    distance_to_hospital_m: Optional[float] = None
    distance_to_medical_facility_m: Optional[float] = None
    distance_to_public_toilet_m: Optional[float] = None
    distance_to_nearest_amenity_m: Optional[float] = None

    # Crime hotspot context (synthetic/proxy)
    nearest_hotspot_distance_m: Optional[float] = None    # synthetic proxy
    nearest_hotspot_intensity: Optional[float] = None     # synthetic proxy

    # Provenance flags
    lighting_data_synthetic: bool = True
    cctv_data_synthetic: bool = True
    mobility_data_synthetic: bool = True
    hotspot_data_synthetic: bool = True
    infrastructure_distances_real: bool = True
    district_baseline_real: bool = True

    # Legacy simple context for dynamic override signals (context-update endpoint)
    footfall_indicator: Optional[float] = None           # override: 0=low, 1=high
    validated_report_signal: Optional[float] = None      # override
    infrastructure_score: Optional[float] = None         # override

    # Nearest lookup metadata
    nearest_segment_id: Optional[str] = None
    nearest_segment_distance_m: Optional[float] = None   # how far the nearest reference segment is


class RiskFeatures(BaseModel):
    """
    13-feature vector for the sakhi XGBoost contextual risk model.
    Feature ORDER must exactly match training (ml/models/train_xgboost.py FEATURES list).

    Leakage exclusions (dependency-based):
    - historical_baseline: derived from same NCRB crime_records.csv as target crime_burden_norm.
    - is_weekend: structurally encodes the WEEKEND_ADJ term in the target formula.
    - is_night, is_late_night, is_evening_peak, is_peak_hour, representative_hour:
      all derived from time_period which is the exact input to TEMPORAL_MULTIPLIER
      used to build 35% of the target. Keeping these would let the model trivially
      reproduce the target's temporal component.

    Data provenance:
    - Road characteristics: OSM geometry / OSRM routing.
    - Environmental (lighting, CCTV, footfall): synthetic proxies, clearly labelled.
    - Infrastructure distances: computed from real GPS coordinates (normalized datasets).
    - Activity context (reduced_activity_context, lighting_relevance): derived from
      footfall proxies only — not from crime statistics.
    """
    # 1. Road characteristics (from OSM geometry/OSRM)
    distance_m: float = Field(default=300.0)
    estimated_travel_time_s: float = Field(default=240.0)

    # 2. Environmental context (synthetic/proxy)
    lighting_score: float = Field(default=50.0)
    cctv_coverage_score: float = Field(default=50.0)
    footfall_proxy: float = Field(default=2000.0)
    contextual_footfall_proxy: float = Field(default=1300.0)

    # 3. Infrastructure distances (real GPS-computed)
    distance_to_police_m: float = Field(default=800.0)
    distance_to_hospital_m: float = Field(default=3000.0)
    distance_to_medical_facility_m: float = Field(default=2000.0)
    distance_to_public_toilet_m: float = Field(default=1200.0)
    distance_to_nearest_amenity_m: float = Field(default=1000.0)

    # 4. Contextual activity indicators (derived from footfall proxy, not crime stats)
    reduced_activity_context: float = Field(default=0.0)
    lighting_relevance: float = Field(default=0.5)


# Legacy 9-feature schema for heuristic fallback
class SimpleRiskFeatures(BaseModel):
    """9-feature vector for the legacy synthetic-only model heuristic fallback."""
    hour_sin: float
    hour_cos: float
    is_weekend: float
    environmental_isolation_indicator: float
    cctv_coverage: float
    police_proximity: float
    transit_access: float
    infrastructure_score: float
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
    """The calculated contextual safety risk score for a segment."""
    segment_id: str
    risk_score: float             # 0 to 100
    confidence_score: float       # 0 to 100
    confidence_level: str         # HIGH, MEDIUM, LOW, Insufficient Data
    model_source: str             # "xgboost_sakhi", "xgboost_legacy", or "heuristic"
    model_version: str            # e.g. "sakhi-v1", "prototype"
    explanation: Optional[RiskExplanation] = None
    factors: Dict[str, Any]
    generated_at: datetime
