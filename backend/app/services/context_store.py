from typing import Dict, List, Any
from app.schemas.journey import JourneyRequest
from app.schemas.ranking import RouteCandidate, RouteRankingResponse
from app.schemas.risk import SegmentContext

class JourneyData:
    def __init__(self, request: JourneyRequest, candidates: List[RouteCandidate], ranking: RouteRankingResponse, segment_contexts: Dict[str, SegmentContext] = None):
        self.request = request
        self.candidates = candidates
        self.ranking = ranking
        self.segment_contexts = segment_contexts or {}

# In-memory prototype state
journey_store: Dict[str, JourneyData] = {}
