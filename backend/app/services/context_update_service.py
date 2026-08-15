from datetime import datetime
from fastapi import HTTPException
from app.schemas.context import ContextUpdateEvent, ContextUpdateResponse
from app.schemas.risk import SegmentContext
from app.services.context_store import journey_store, JourneyData
from app.services.risk.risk_service import RiskService
from app.services.routing.route_ranking_service import RouteRankingService

class ContextUpdateService:
    def __init__(self):
        self.risk_service = RiskService()
        self.ranking_service = RouteRankingService()

    def process_update(self, journey_id: str, event: ContextUpdateEvent) -> ContextUpdateResponse:
        if journey_id not in journey_store:
            raise HTTPException(status_code=404, detail="Journey not found in active prototype state")
            
        journey_data = journey_store[journey_id]
        candidates = journey_data.candidates
        
        # 1. Find segment in candidates
        target_segment = None
        target_candidate = None
        for cand in candidates:
            for seg in cand.segments:
                if seg.segment_id == event.segment_id:
                    target_segment = seg
                    target_candidate = cand
                    break
            if target_segment:
                break
                
        if not target_segment:
            raise HTTPException(status_code=404, detail="Segment not found in this journey")
            
        # Keep track of before state
        safest_before = journey_data.ranking.safest_route.route_id if journey_data.ranking.safest_route else None
        before_risk = target_segment.risk_score
        before_confidence = target_segment.confidence_score
        
        # 2. Apply context update
        # For prototype, we mutate a temporary SegmentContext and map the event
        context = SegmentContext(departure_time=journey_data.request.departure_time or datetime.now())
        
        # Map event types to contextual signal overrides
        if event.active:
            severity_norm = min(100.0, max(0.0, event.severity)) / 100.0
            if event.event_type == "validated_report":
                context.validated_report_signal = severity_norm
            elif event.event_type == "environmental_change":
                context.footfall_indicator = 1.0 - severity_norm # High severity = low footfall (high isolation)
            elif event.event_type == "infrastructure_change":
                context.infrastructure_score = 1.0 - severity_norm
            elif event.event_type == "crowd_change":
                context.footfall_indicator = 1.0 - severity_norm

        # 3. Recalculate Risk, Confidence, SHAP
        risk_score = self.risk_service.calculate_risk(target_segment, context)
        target_segment.risk_score = risk_score.risk_score
        target_segment.confidence_score = risk_score.confidence_score
        target_segment.explanation = risk_score.explanation.model_dump() if risk_score.explanation else None
        
        # 4. Reaggregate Metrics for the candidate
        target_candidate.metrics = self.ranking_service.aggregate_metrics(target_candidate.segments)
        
        # 5. Rerank routes
        new_ranking = self.ranking_service.rank_routes(journey_id, candidates)
        journey_data.ranking = new_ranking
        
        safest_after = new_ranking.safest_route.route_id if new_ranking.safest_route else None
        rerouted = (safest_before != safest_after) and (safest_after is not None)
        
        reason = "Contextual safety risk changed on segment " + event.segment_id
        if not rerouted:
            reason = "Current route remains preferred despite contextual update."
            if len(candidates) == 1:
                reason = "Only one route candidate exists. Ranking unchanged."
                
        return ContextUpdateResponse(
            journey_id=journey_id,
            updated_segment_id=event.segment_id,
            event=event,
            before={
                "risk": before_risk,
                "confidence": before_confidence,
                "safest_route_id": safest_before
            },
            after={
                "risk": target_segment.risk_score,
                "confidence": target_segment.confidence_score,
                "safest_route_id": safest_after
            },
            rerouted=rerouted,
            reason=reason
        )
