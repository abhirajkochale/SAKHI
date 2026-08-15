from datetime import datetime, timezone
from app.schemas.journey import JourneySegment
from app.schemas.risk import SegmentContext, RiskScore
from app.services.risk.feature_service import FeatureExtractionService
from app.services.risk.baseline_service import HistoricalBaselineService
from app.services.risk.confidence_service import ConfidenceService

class RiskService:
    """
    Risk calculation service using a transparent deterministic prototype heuristic.
    This baseline combines available contextual factors transparently.
    """
    def __init__(self):
        self.feature_service = FeatureExtractionService()
        self.baseline_service = HistoricalBaselineService()
        self.confidence_service = ConfidenceService()

    def calculate_risk(self, segment: JourneySegment, context: SegmentContext) -> RiskScore:
        # 1. Calculate Confidence based on true evidence availability BEFORE filling defaults
        conf_score, conf_level = self.confidence_service.calculate_confidence(context)

        # Ensure historical baseline is populated if missing, using the baseline service
        if context.historical_baseline is None:
            context.historical_baseline = self.baseline_service.get_baseline(segment)

        # 2. Extract Features
        features = self.feature_service.extract_features(segment, context)

        # 3. Apply Prototype Heuristic Weights (Not scientifically validated)
        # Higher score = greater safety concern
        
        # Base risk from historical regional prior
        base_risk = features.historical_baseline * 40.0
        
        # Environmental factors that increase concern
        isolation_risk = features.environmental_isolation_indicator * 30.0
        
        # Mitigating infrastructure factors that decrease concern (so we subtract them or take inverse)
        lack_of_infrastructure = (1.0 - features.infrastructure_score) * 15.0
        lack_of_cctv = (1.0 - features.cctv_coverage) * 10.0
        lack_of_police = (1.0 - features.police_proximity) * 5.0
        
        # Night time penalty (simplistic hour heuristic for prototype)
        # cos(hour) is 1.0 at midnight, -1.0 at noon
        time_penalty = max(0.0, features.hour_cos) * 10.0
        
        # Validate reports (if any, adds direct concern)
        report_risk = features.validated_report_signal * 20.0
        
        raw_risk = base_risk + isolation_risk + lack_of_infrastructure + lack_of_cctv + lack_of_police + time_penalty + report_risk
        
        # Normalize to 0-100
        final_risk = min(100.0, max(0.0, raw_risk))
        
        factors = {
            "historical_prior_contribution": base_risk,
            "isolation_contribution": isolation_risk,
            "infrastructure_deficit_contribution": lack_of_infrastructure,
            "cctv_deficit_contribution": lack_of_cctv,
            "police_deficit_contribution": lack_of_police,
            "time_penalty": time_penalty,
            "report_risk": report_risk
        }
        
        return RiskScore(
            segment_id=segment.segment_id,
            risk_score=final_risk,
            confidence_score=conf_score,
            confidence_level=conf_level,
            factors=factors,
            generated_at=datetime.now(timezone.utc)
        )
