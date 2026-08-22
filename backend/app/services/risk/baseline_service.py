from app.schemas.journey import JourneySegment
from app.models.database import SessionLocal
from app.models.route_segment import PersistentRouteSegment

class HistoricalBaselineService:
    """
    Provides a dynamic historical baseline pulled from the database, factoring in
    recent user incident reports.
    """
    def get_baseline(self, segment: JourneySegment) -> float:
        db = SessionLocal()
        try:
            db_segment = db.query(PersistentRouteSegment).filter(PersistentRouteSegment.segment_id == segment.segment_id).first()
            if db_segment:
                # Assuming base_risk_score is 0-100, we normalize it to 0-1
                return min(1.0, max(0.0, db_segment.base_risk_score / 100.0))
            return 0.5
        finally:
            db.close()
