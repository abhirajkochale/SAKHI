"""
ConfidenceService
=================
Calculates a confidence score that is INDEPENDENT of the risk score.

Confidence reflects evidence quality/availability, NOT the magnitude of risk.
A segment with high risk and high confidence is a well-supported assessment.
A segment with low risk and low confidence means we don't know much.

Formula (matches ml/models/build_confidence.py):
  confidence = 0.45 * data_quality + 0.35 * mapping_quality + 0.20 * infrastructure_quality

- data_quality: penalises synthetic/proxy feature usage
- mapping_quality: based on nearest reference segment distance
- infrastructure_quality: reward for nearby real infrastructure

IMPORTANT: Confidence does NOT increase risk scores. It is an independent
uncertainty measure shown alongside risk.
"""

from app.schemas.risk import SegmentContext


class ConfidenceService:
    """
    Calculates confidence score (0-100) and level (HIGH/MEDIUM/LOW) for a
    segment's risk assessment.
    """

    def calculate_confidence(self, context: SegmentContext) -> tuple[float, str]:
        """
        Returns (confidence_score: float, confidence_level: str).

        Inputs used:
        - Which data sources are synthetic vs real (provenance flags)
        - Whether departure time is known
        - How far the nearest reference segment is (lookup quality)
        - Whether real infrastructure data was used
        """

        # ── Data quality component (penalise synthetic proxy usage) ──────
        # Each synthetic source reduces confidence by ~11 points
        # (4 sources * 11 = 44 point penalty if all synthetic → score = 56 base)
        data_quality = 100.0
        if context.lighting_data_synthetic:
            data_quality -= 11.0
        if context.cctv_data_synthetic:
            data_quality -= 11.0
        if context.mobility_data_synthetic:
            data_quality -= 11.0
        if context.hotspot_data_synthetic:
            data_quality -= 11.0
        if context.departure_time is None:
            data_quality -= 10.0
        data_quality = max(0.0, data_quality)

        # ── Mapping quality component (how well we know the location) ────
        # If nearest reference segment is within 500m → high mapping quality
        # If within 2km → medium. Beyond 5km → low.
        ref_dist = context.nearest_segment_distance_m
        if ref_dist is None:
            mapping_quality = 50.0   # Unknown → moderate assumption
        elif ref_dist < 500:
            mapping_quality = 100.0
        elif ref_dist < 2000:
            mapping_quality = 70.0
        elif ref_dist < 5000:
            mapping_quality = 45.0
        else:
            mapping_quality = 25.0   # Far from any reference segment

        # ── Infrastructure quality (real GPS data used) ───────────────────
        # If real police/hospital distances were computed → good
        infra_quality = 100.0 if context.infrastructure_distances_real else 50.0
        if context.district_baseline_real:
            infra_quality = min(100.0, infra_quality + 0.0)   # Already full if real
        else:
            infra_quality -= 20.0
        infra_quality = max(0.0, infra_quality)

        # ── Weighted confidence score ─────────────────────────────────────
        confidence_score = (
            0.45 * data_quality
            + 0.35 * mapping_quality
            + 0.20 * infra_quality
        )
        confidence_score = round(max(0.0, min(100.0, confidence_score)), 2)

        # ── Confidence level ──────────────────────────────────────────────
        if confidence_score >= 70.0:
            level = "HIGH"
        elif confidence_score >= 40.0:
            level = "MEDIUM"
        elif confidence_score > 0.0:
            level = "LOW"
        else:
            level = "Insufficient Data"

        return confidence_score, level
