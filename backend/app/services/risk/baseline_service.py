from app.schemas.journey import JourneySegment

class HistoricalBaselineService:
    """
    Provides a deterministic historical baseline.
    This is NOT a crime prediction, but acts as a regional prior/context signal.
    """
    def get_baseline(self, segment: JourneySegment) -> float:
        # For the prototype, return a static regional prior deterministic value
        return 0.5
