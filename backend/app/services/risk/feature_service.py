import math
from app.schemas.journey import JourneySegment
from app.schemas.risk import SegmentContext, RiskFeatures

class FeatureExtractionService:
    def extract_features(self, segment: JourneySegment, context: SegmentContext) -> RiskFeatures:
        # Temporal features
        hour_sin = 0.0
        hour_cos = 0.0
        is_weekend = 0.0
        if context.departure_time:
            hour = context.departure_time.hour + context.departure_time.minute / 60.0
            hour_sin = math.sin(2 * math.pi * hour / 24.0)
            hour_cos = math.cos(2 * math.pi * hour / 24.0)
            is_weekend = 1.0 if context.departure_time.weekday() >= 5 else 0.0

        # Environmental isolation indicator based on footfall
        # low footfall indicator -> high isolation
        isolation = 1.0
        if context.footfall_indicator is not None:
            isolation = 1.0 - context.footfall_indicator

        return RiskFeatures(
            hour_sin=hour_sin,
            hour_cos=hour_cos,
            is_weekend=is_weekend,
            environmental_isolation_indicator=isolation,
            cctv_coverage=context.cctv_coverage or 0.0,
            police_proximity=context.police_proximity or 0.0,
            transit_access=context.transit_access or 0.0,
            infrastructure_score=context.infrastructure_score or 0.5, # default neutral
            historical_baseline=context.historical_baseline or 0.5, # default neutral
            validated_report_signal=context.validated_report_signal or 0.0
        )
