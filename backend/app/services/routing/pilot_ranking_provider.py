"""Coverage-aware adapter for the audited Connaught Place safety-route pilot."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Optional, Tuple

from app.schemas.journey import JourneySegment


class PilotRankingProvider:
    """Read prototype scores only inside their documented geographic coverage.

    The pilot is intentionally not used outside Connaught Place.  Returning
    ``None`` tells the caller to keep the established city-wide ranker.
    """

    def __init__(self) -> None:
        self._router = None
        self._load_attempted = False

    def _load(self) -> bool:
        if self._load_attempted:
            return self._router is not None
        self._load_attempted = True

        project_root = Path(__file__).resolve().parents[4] / "ml" / "safety_route"
        source_dir = project_root / "src"
        if not source_dir.exists():
            return False
        sys.path.insert(0, str(source_dir))
        try:
            from safety_route.prototype_router import PrototypeRouter

            self._router = PrototypeRouter(project_root=project_root)
            return True
        except (ImportError, OSError, ValueError):
            # Optional spatial dependencies or pilot artefacts are unavailable.
            # The caller will retain the existing, tested ranking behavior.
            self._router = None
            return False

    def score_segments(self, segments: Iterable[JourneySegment]) -> Optional[Tuple[float, float, float]]:
        """Return (duration-weighted risk, confidence, maximum risk) for a pilot route."""
        segment_list = list(segments)
        if not segment_list or not self._load():
            return None

        router = self._router
        if any(
            not router.is_covered(segment.start_location.latitude, segment.start_location.longitude)
            or not router.is_covered(segment.end_location.latitude, segment.end_location.longitude)
            for segment in segment_list
        ):
            return None

        total_duration = sum(max(segment.duration_s, 0.0) for segment in segment_list)
        weighted_risk = 0.0
        weighted_confidence = 0.0
        max_risk = 0.0

        for segment in segment_list:
            midpoint_lat = (segment.start_location.latitude + segment.end_location.latitude) / 2
            midpoint_lon = (segment.start_location.longitude + segment.end_location.longitude) / 2
            score = router.score_point(midpoint_lat, midpoint_lon)
            if score is None:
                return None
            risk, confidence = score
            duration = max(segment.duration_s, 0.0)
            weighted_risk += risk * duration
            weighted_confidence += confidence * duration
            max_risk = max(max_risk, risk)

        divisor = total_duration or float(len(segment_list))
        if total_duration == 0:
            weighted_risk = sum(router.score_point(
                (segment.start_location.latitude + segment.end_location.latitude) / 2,
                (segment.start_location.longitude + segment.end_location.longitude) / 2,
            )[0] for segment in segment_list)
            weighted_confidence = sum(router.score_point(
                (segment.start_location.latitude + segment.end_location.latitude) / 2,
                (segment.start_location.longitude + segment.end_location.longitude) / 2,
            )[1] for segment in segment_list)
        return weighted_risk / divisor, weighted_confidence / divisor, max_risk
