"""
FeatureExtractionService
========================
Builds the 13-feature RiskFeatures vector for the sakhi XGBoost model
from a JourneySegment + SegmentContext.

Feature sources:
  1. Road characteristics: from segment geometry / OSRM
  2. Environmental proxies (SYNTHETIC): nearest lighting/CCTV/mobility measurement
  3. Infrastructure distances (real GPS-computed): police/hospital/amenity
  4. Activity context: derived from footfall proxies only

Excluded from model vector (dependency-based leakage):
  historical_baseline   -- same NCRB source as target's crime_burden_norm
  is_weekend            -- encodes target's WEEKEND_ADJ directly
  is_night, is_late_night, is_evening_peak, is_peak_hour, representative_hour
                        -- encode target's TEMPORAL_MULTIPLIER directly

Feature ORDER must match ml/models/train_xgboost.py FEATURES list exactly.
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any

from app.schemas.journey import JourneySegment
from app.schemas.risk import RiskFeatures, SegmentContext
from app.services.risk.segment_lookup_service import get_segment_lookup_service


# ── Temporal period definitions (must match build_temporal_dataset.py) ─────────

def _get_temporal_period(hour: int) -> str:
    """Map hour of day to time period label used during training."""
    if 6 <= hour < 10:
        return "Morning"
    elif 10 <= hour < 17:
        return "Day"
    elif 17 <= hour < 22:
        return "Evening"
    elif 22 <= hour < 24:
        return "Night"
    else:  # 0-6
        return "Late Night"


def _temporal_footfall_multiplier(period: str) -> float:
    """Footfall multiplier by period — matches build_temporal_dataset.py."""
    return {
        "Morning": 0.65,
        "Day": 0.55,
        "Evening": 1.00,
        "Night": 0.35,
        "Late Night": 0.20,
    }.get(period, 0.55)


def _build_temporal_features(dt: datetime, footfall_proxy: float) -> Dict[str, Any]:
    """Derive all temporal features from a departure datetime."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    hour = dt.hour
    period = _get_temporal_period(hour)
    multiplier = _temporal_footfall_multiplier(period)

    is_night = int(period in ("Night", "Late Night"))
    is_late_night = int(period == "Late Night")
    is_evening_peak = int(period == "Evening")
    is_peak_hour = int(period in ("Morning", "Evening"))
    is_weekend = int(dt.weekday() >= 5)          # Saturday=5, Sunday=6

    contextual_footfall = footfall_proxy * multiplier

    # reduced_activity_context = footfall has dropped more than 50% from evening reference
    reduced_activity = int(contextual_footfall < footfall_proxy * 0.5)

    # lighting_relevance: night = 1.0, day = 0.5 (matches build_temporal_dataset.py)
    lighting_relevance = 1.0 if is_night else 0.5

    return {
        "representative_hour": float(hour),
        "is_night": float(is_night),
        "is_late_night": float(is_late_night),
        "is_evening_peak": float(is_evening_peak),
        "is_weekend": float(is_weekend),
        "is_peak_hour": float(is_peak_hour),
        "contextual_footfall_proxy": round(contextual_footfall, 2),
        "reduced_activity_context": float(reduced_activity),
        "lighting_relevance": lighting_relevance,
    }


class FeatureExtractionService:
    """
    Extracts the complete 13-feature vector from a JourneySegment + SegmentContext.
    """

    def __init__(self):
        self._lookup = get_segment_lookup_service()

    def extract(
        self,
        segment: JourneySegment,
        context: SegmentContext,
    ) -> RiskFeatures:
        """
        Build the 13-feature RiskFeatures from segment + context.

        Priority for feature values:
        1. Explicit overrides on context (dynamic context-update signals)
        2. Pre-computed context from SegmentLookupService (populated in osrm_client)
        3. On-demand spatial computation from SegmentLookupService
        4. Safe defaults (clearly documented)
        """

        # ── Segment midpoint ──────────────────────────────────────────────
        lat = context.segment_lat
        lon = context.segment_lon
        if lat is None or lon is None:
            lat = (segment.start_location.latitude + segment.end_location.latitude) / 2.0
            lon = (segment.start_location.longitude + segment.end_location.longitude) / 2.0

        # ── 1. Road characteristics ───────────────────────────────────────
        distance_m = context.distance_m or float(segment.distance_m or 300.0)
        estimated_travel_time_s = context.estimated_travel_time_s or float(segment.duration_s or 240.0)

        # ── 3. Environmental proxies (synthetic) ──────────────────────────
        if context.lighting_score is not None:
            lighting_score = context.lighting_score
        else:
            proxies = self._lookup.get_synthetic_proxies(lat, lon)
            lighting_score = proxies["lighting_score"]

        if context.cctv_coverage_score is not None:
            cctv_coverage_score = context.cctv_coverage_score
        else:
            proxies = self._lookup.get_synthetic_proxies(lat, lon)
            cctv_coverage_score = proxies["cctv_coverage_score"]

        if context.footfall_proxy is not None:
            footfall_proxy = context.footfall_proxy
        else:
            proxies = self._lookup.get_synthetic_proxies(lat, lon)
            footfall_proxy = proxies["footfall_proxy"]
            # Apply footfall_indicator override if set (context-update signal)
        if context.footfall_indicator is not None:
            # footfall_indicator is 0.0-1.0; scale to footfall_proxy range
            footfall_proxy = footfall_proxy * (0.2 + 0.8 * float(context.footfall_indicator))

        # ── 4. Infrastructure distances (real) ────────────────────────────
        if context.distance_to_police_m is not None:
            infra = {
                "distance_to_police_m": context.distance_to_police_m,
                "distance_to_hospital_m": context.distance_to_hospital_m or 3000.0,
                "distance_to_medical_facility_m": context.distance_to_medical_facility_m or 2000.0,
                "distance_to_public_toilet_m": context.distance_to_public_toilet_m or 1200.0,
                "distance_to_nearest_amenity_m": context.distance_to_nearest_amenity_m or 1000.0,
            }
        else:
            infra = self._lookup.get_infrastructure_distances(lat, lon)
            # Apply overrides from context if set
            if context.distance_to_police_m is not None:
                infra["distance_to_police_m"] = context.distance_to_police_m
            if context.distance_to_hospital_m is not None:
                infra["distance_to_hospital_m"] = context.distance_to_hospital_m


        # ── 4. Temporal context (compute but only use non-leaking outputs) ──
        departure = context.departure_time or datetime.now(timezone.utc)
        temporal = _build_temporal_features(departure, footfall_proxy)

        # Use pre-computed contextual_footfall if available from context
        if context.contextual_footfall_proxy is not None:
            temporal["contextual_footfall_proxy"] = context.contextual_footfall_proxy

        # ── Assemble RiskFeatures (13 features, leakage-free) ─────────────
        return RiskFeatures(
            distance_m=float(distance_m),
            estimated_travel_time_s=float(estimated_travel_time_s),
            lighting_score=float(lighting_score),
            cctv_coverage_score=float(cctv_coverage_score),
            footfall_proxy=float(footfall_proxy),
            contextual_footfall_proxy=float(temporal["contextual_footfall_proxy"]),
            distance_to_police_m=float(infra["distance_to_police_m"]),
            distance_to_hospital_m=float(infra["distance_to_hospital_m"]),
            distance_to_medical_facility_m=float(infra["distance_to_medical_facility_m"]),
            distance_to_public_toilet_m=float(infra["distance_to_public_toilet_m"]),
            distance_to_nearest_amenity_m=float(infra["distance_to_nearest_amenity_m"]),
            reduced_activity_context=float(temporal["reduced_activity_context"]),
            lighting_relevance=float(temporal["lighting_relevance"]),
        )
