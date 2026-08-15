from typing import Dict, List, Any
from app.schemas.journey import JourneyRequest
from app.schemas.ranking import RouteCandidate, RouteRankingResponse

class JourneyData:
    def __init__(self, request: JourneyRequest, candidates: List[RouteCandidate], ranking: RouteRankingResponse):
        self.request = request
        self.candidates = candidates
        self.ranking = ranking

# In-memory prototype state
journey_store: Dict[str, JourneyData] = {}
