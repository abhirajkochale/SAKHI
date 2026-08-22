"""
HistoricalBaselineService
=========================
Provides district-level historical crime baselines from real NCRB data.

IMPORTANT: Crime data is available at DISTRICT LEVEL ONLY.
This service maps a journey segment's coordinates to the nearest district
and returns that district's historical baseline values.

It does NOT invent street-level crime data.
It does NOT represent the baseline as a crime prediction.
"""

from app.schemas.journey import JourneySegment
from app.services.risk.segment_lookup_service import get_segment_lookup_service
from app.models.database import SessionLocal
from app.models.route_segment import PersistentRouteSegment


class HistoricalBaselineService:
    """
    Returns real NCRB-derived district historical baseline values,
    overridable by dynamic historical baselines pulled from the database 
    based on recent user incident reports.
    """

    def __init__(self):
        self._lookup = get_segment_lookup_service()

    def get_baseline(self, segment: JourneySegment) -> float:
        """
        Returns the normalized historical baseline (0-100).
        Checks the database first for dynamic updates, falls back to NCRB district data.
        """
        db = SessionLocal()
        try:
            db_segment = db.query(PersistentRouteSegment).filter(PersistentRouteSegment.segment_id == segment.segment_id).first()
            if db_segment:
                return float(db_segment.base_risk_score)
        finally:
            db.close()
            
        district = self._get_district(segment)
        stats = self._lookup.get_district_baseline(district)
        return stats.get("historical_baseline", 50.0)

    def get_full_district_stats(self, segment: JourneySegment) -> dict:
        """
        Returns all district-level historical statistics for this segment.
        Includes baseline, cases_per_100k, trend slope, etc.
        """
        district = self._get_district(segment)
        return self._lookup.get_district_baseline(district)

    def _get_district(self, segment: JourneySegment) -> str:
        """Determine district from segment midpoint coordinates."""
        try:
            lat = (segment.start_location.latitude + segment.end_location.latitude) / 2.0
            lon = (segment.start_location.longitude + segment.end_location.longitude) / 2.0
            return self._lookup.get_district(lat, lon)
        except Exception:
            return "Unknown"
