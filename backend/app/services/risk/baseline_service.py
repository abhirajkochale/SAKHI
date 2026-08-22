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


class HistoricalBaselineService:
    """
    Returns real NCRB-derived district historical baseline values.

    Source: ml/data/processed/district_historical_baseline.csv
    Resolution: District level (11 Delhi districts)
    Data: Real NCRB Crime in India + Delhi Police Statistical Handbook

    District assignment: via nearest police station coordinate.
    """

    def __init__(self):
        self._lookup = get_segment_lookup_service()

    def get_baseline(self, segment: JourneySegment) -> float:
        """
        Returns the normalized historical baseline (0-100) for the
        district this segment belongs to.

        Used as a regional context prior — NOT a street-level crime prediction.
        """
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
