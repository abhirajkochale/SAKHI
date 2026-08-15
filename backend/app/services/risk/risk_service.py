from datetime import datetime, timezone
from app.schemas.journey import JourneySegment
from app.schemas.risk import SegmentContext, RiskScore, RiskExplanation
from app.services.risk.feature_service import FeatureExtractionService
from app.services.risk.baseline_service import HistoricalBaselineService
from app.services.risk.confidence_service import ConfidenceService
from app.services.risk.ml_model_service import MLModelService
from app.services.risk.shap_service import SHAPService

class RiskService:
    """
    Risk calculation service using an XGBoost ML model or falling back to a 
    transparent deterministic prototype heuristic.
    """
    def __init__(self):
        self.feature_service = FeatureExtractionService()
        self.baseline_service = HistoricalBaselineService()
        self.confidence_service = ConfidenceService()
        self.ml_service = MLModelService()
        self.shap_service = SHAPService(self.ml_service)

    def calculate_risk(self, segment: JourneySegment, context: SegmentContext) -> RiskScore:
        # 1. Calculate Confidence based on true evidence availability BEFORE filling defaults
        conf_score, conf_level = self.confidence_service.calculate_confidence(context)

        # Ensure historical baseline is populated if missing, using the baseline service
        if context.historical_baseline is None:
            context.historical_baseline = self.baseline_service.get_baseline(segment)

        # 2. Extract Features
        features = self.feature_service.extract_features(segment, context)

        # 3. XGBoost ML Inference Attempt
        ml_score = self.ml_service.predict(features)
        
        if ml_score is not None:
            final_risk = ml_score
            model_source = self.ml_service.get_metadata().get("model_source", "xgboost")
            model_version = self.ml_service.get_metadata().get("model_version", "unknown")
            factors = {"ml_inference": True}
            explanation = self.shap_service.explain(features, final_risk)
        else:
            # 4. Fallback to Prototype Heuristic
            # Higher score = greater safety concern
            base_risk = features.historical_baseline * 40.0
            isolation_risk = features.environmental_isolation_indicator * 30.0
            lack_of_infrastructure = (1.0 - features.infrastructure_score) * 15.0
            lack_of_cctv = (1.0 - features.cctv_coverage) * 10.0
            lack_of_police = (1.0 - features.police_proximity) * 5.0
            time_penalty = max(0.0, features.hour_cos) * 10.0
            report_risk = features.validated_report_signal * 20.0
            
            raw_risk = base_risk + isolation_risk + lack_of_infrastructure + lack_of_cctv + lack_of_police + time_penalty + report_risk
            final_risk = min(100.0, max(0.0, raw_risk))
            
            model_source = "heuristic"
            model_version = "prototype"
            factors = {
                "historical_prior_contribution": base_risk,
                "isolation_contribution": isolation_risk,
                "infrastructure_deficit_contribution": lack_of_infrastructure,
                "cctv_deficit_contribution": lack_of_cctv,
                "police_deficit_contribution": lack_of_police,
                "time_penalty": time_penalty,
                "report_risk": report_risk
            }
            explanation = RiskExplanation(
                available=False,
                reason="SHAP explanation unavailable because XGBoost model is not active."
            )
        
        return RiskScore(
            segment_id=segment.segment_id,
            risk_score=final_risk,
            confidence_score=conf_score,
            confidence_level=conf_level,
            model_source=model_source,
            model_version=model_version,
            explanation=explanation,
            factors=factors,
            generated_at=datetime.now(timezone.utc)
        )
