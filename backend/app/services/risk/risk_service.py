"""
RiskService
===========
Orchestrates the full contextual safety risk pipeline for a JourneySegment:

  1. Confidence (evidence quality — independent of risk)
  2. Spatial context enrichment (district, infrastructure distances, synthetic proxies)
  3. Feature extraction (27 features for sakhi model)
  4. XGBoost inference (sakhi primary model)
  5. SHAP explanation
  6. Heuristic fallback if model unavailable

IMPORTANT:
- The risk score is a contextual safety indicator (0-100), not a crime prediction.
- The training target is prototype_risk_target, target_is_observed_crime = False.
- Confidence is calculated BEFORE filling feature defaults.
"""

from datetime import datetime, timezone

from app.schemas.journey import JourneySegment
from app.schemas.risk import SegmentContext, RiskScore, RiskExplanation, RiskFeatures
from app.services.risk.feature_service import FeatureExtractionService
from app.services.risk.baseline_service import HistoricalBaselineService
from app.services.risk.confidence_service import ConfidenceService
from app.services.risk.ml_model_service import MLModelService
from app.services.risk.shap_service import SHAPService
from app.services.risk.segment_lookup_service import get_segment_lookup_service


class RiskService:
    """
    Contextual safety risk calculator.
    Primary model: sakhi XGBoost 27-feature model.
    Fallback: deterministic prototype heuristic.
    """

    def __init__(self):
        self.feature_service = FeatureExtractionService()
        self.baseline_service = HistoricalBaselineService()
        self.confidence_service = ConfidenceService()
        self.ml_service = MLModelService()
        self.shap_service = SHAPService(self.ml_service)
        self._lookup = get_segment_lookup_service()

    def calculate_risk(self, segment: JourneySegment, context: SegmentContext) -> RiskScore:
        """
        Calculate contextual safety risk for a segment.
        Returns RiskScore with risk, confidence, model source, and SHAP explanation.
        """

        # ── 0. Enrich context with spatial data if not already set ────────
        lat = context.segment_lat
        lon = context.segment_lon
        if lat is None or lon is None:
            lat = (segment.start_location.latitude + segment.end_location.latitude) / 2.0
            lon = (segment.start_location.longitude + segment.end_location.longitude) / 2.0
            context.segment_lat = lat
            context.segment_lon = lon

        # Determine district (used for confidence + baseline)
        if context.district is None:
            context.district = self._lookup.get_district(lat, lon)

        # Find nearest reference segment (used for confidence mapping quality)
        if context.nearest_segment_distance_m is None:
            _, ref_dist = self._lookup.get_nearest_reference_segment(lat, lon)
            context.nearest_segment_distance_m = ref_dist if ref_dist != float("inf") else None

        # ── 1. Confidence (BEFORE filling defaults) ───────────────────────
        conf_score, conf_level = self.confidence_service.calculate_confidence(context)

        # ── 2. Feature extraction (27-feature vector) ─────────────────────
        features = self.feature_service.extract(segment, context)

        # ── 3. Primary XGBoost inference ──────────────────────────────────
        ml_score = self.ml_service.predict(features)

        if ml_score is not None:
            final_risk = ml_score
            model_source = self.ml_service.get_model_source()
            model_version = self.ml_service.get_metadata().get("model_version", "sakhi-v1")
            explanation = self.shap_service.explain(features, final_risk)
            factors = {
                "ml_inference": True,
                "model_source": model_source,
                "district": context.district,
                "historical_baseline": features.historical_baseline,
                "is_night": bool(features.is_night),
                "lighting_score": features.lighting_score,
                "cctv_coverage_score": features.cctv_coverage_score,
                "distance_to_police_m": features.distance_to_police_m,
            }

        else:
            # ── 4. Heuristic fallback ─────────────────────────────────────
            # Based on 27-feature inputs but using simple linear combination
            norm_baseline = features.historical_baseline / 100.0  # 0-1
            norm_lighting = (100.0 - features.lighting_score) / 100.0  # invert: lower lighting = riskier
            norm_police = min(1.0, features.distance_to_police_m / 3000.0)   # further = riskier
            norm_cctv = (100.0 - features.cctv_coverage_score) / 100.0
            norm_time = features.is_night * 0.3 + features.is_late_night * 0.2 + features.is_evening_peak * 0.1
            norm_hotspot = max(0.0, 1.0 - features.nearest_hotspot_distance_m / 5000.0)
            report_risk = (
                (context.validated_report_signal or 0.0) * 20.0
                if context.validated_report_signal is not None else 0.0
            )

            raw = (
                norm_baseline * 35.0
                + norm_lighting * 15.0
                + norm_police * 10.0
                + norm_cctv * 10.0
                + norm_time * 20.0
                + norm_hotspot * 10.0
                + report_risk
            )
            final_risk = max(0.0, min(100.0, raw))

            model_source = "heuristic"
            model_version = "prototype"
            explanation = RiskExplanation(
                available=False,
                reason="XGBoost sakhi model not available. Deterministic heuristic used.",
            )
            factors = {
                "ml_inference": False,
                "model_source": "heuristic",
                "district": context.district,
                "historical_baseline_contribution": round(norm_baseline * 35.0, 2),
                "lighting_deficit_contribution": round(norm_lighting * 15.0, 2),
                "police_distance_contribution": round(norm_police * 10.0, 2),
                "cctv_deficit_contribution": round(norm_cctv * 10.0, 2),
                "temporal_contribution": round(norm_time * 20.0, 2),
                "hotspot_proximity_contribution": round(norm_hotspot * 10.0, 2),
                "report_contribution": round(report_risk, 2),
            }

        return RiskScore(
            segment_id=segment.segment_id,
            risk_score=round(final_risk, 2),
            confidence_score=conf_score,
            confidence_level=conf_level,
            model_source=model_source,
            model_version=model_version,
            explanation=explanation,
            factors=factors,
            generated_at=datetime.now(timezone.utc),
        )
