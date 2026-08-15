from app.schemas.risk import SegmentContext

class ConfidenceService:
    """
    Confidence must be SEPARATE from risk.
    It reflects evidence availability / quality.
    """
    def calculate_confidence(self, context: SegmentContext) -> tuple[float, str]:
        score = 100.0
        
        # Deduct points for missing context
        if context.departure_time is None:
            score -= 20.0
        if context.historical_baseline is None:
            score -= 20.0
        if context.footfall_indicator is None:
            score -= 20.0
        if context.cctv_coverage is None:
            score -= 10.0
        if context.police_proximity is None:
            score -= 10.0
        if context.infrastructure_score is None:
            score -= 10.0
        if context.transit_access is None:
            score -= 10.0
            
        score = max(0.0, score)
        
        if score >= 75.0:
            level = "HIGH"
        elif score >= 50.0:
            level = "MEDIUM"
        elif score > 0.0:
            level = "LOW"
        else:
            level = "Insufficient Data"
            
        return score, level
