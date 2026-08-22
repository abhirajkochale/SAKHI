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

    def _apply_event_to_context(self, context: SegmentContext, event: ContextUpdateEvent) -> None:
        """Apply the event signal override onto an existing SegmentContext in-place."""
        if not event.active:
            return
        severity_norm = min(100.0, max(0.0, event.severity)) / 100.0
        if event.event_type == "validated_report":
            # A validated safety report REDUCES perceived risk for this corridor.
            # We lower validated_report_signal to reflect the report (safety confirmation).
            context.validated_report_signal = 1.0 - severity_norm
        elif event.event_type == "environmental_change":
            context.footfall_indicator = 1.0 - severity_norm
        elif event.event_type == "infrastructure_change":
            context.infrastructure_score = 1.0 - severity_norm
        elif event.event_type == "crowd_change":
            context.footfall_indicator = 1.0 - severity_norm

    async def process_update(self, journey_id: str, event: ContextUpdateEvent) -> ContextUpdateResponse:
        if journey_id not in journey_store:
            raise HTTPException(status_code=404, detail="Journey not found in active prototype state")
            
        journey_data = journey_store[journey_id]
        candidates = journey_data.candidates
        
        # 1. Find segment and its parent candidate
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
            
        # Keep before state
        safest_before = journey_data.ranking.safest_route.route_id if journey_data.ranking.safest_route else None
        before_risk = target_segment.risk_score
        before_confidence = target_segment.confidence_score
        
        # 2. Apply the safety event to ALL segments of the target candidate route.
        #    Semantic: a safety report on a segment represents improved situational awareness
        #    for the whole route corridor, not just the one clicked segment.
        #    This ensures the route-level risk score genuinely changes enough to affect ranking.
        for seg in target_candidate.segments:
            # Get or create a persistent context for each segment, preserving existing signals
            ctx = journey_data.segment_contexts.get(seg.segment_id)
            if not ctx:
                ctx = SegmentContext(departure_time=journey_data.request.departure_time or datetime.now())
                journey_data.segment_contexts[seg.segment_id] = ctx

            # Apply the event override
            self._apply_event_to_context(ctx, event)
            
            # Recalculate risk with the merged context
            result = self.risk_service.calculate_risk(seg, ctx)
            seg.risk_score = result.risk_score
            seg.confidence_score = result.confidence_score
            # Only store full explanation for the target segment (the one displayed in SegmentSafetyPanel)
            if seg.segment_id == event.segment_id:
                seg.explanation = result.explanation.model_dump() if result.explanation else None

        # 3. Re-aggregate metrics for the updated candidate
        target_candidate.metrics = self.ranking_service.aggregate_metrics(target_candidate.segments)
        
        # 4. Re-rank all routes with the fresh metrics
        new_ranking = self.ranking_service.rank_routes(journey_id, candidates)
        journey_data.ranking = new_ranking
        
        safest_after = new_ranking.safest_route.route_id if new_ranking.safest_route else None
        rerouted = (safest_before != safest_after) and (safest_after is not None)
        
        reason = "Contextual safety improved on route corridor — routes re-ranked."
        if not rerouted:
            reason = "Current route remains preferred despite contextual update."
            if len(candidates) == 1:
                reason = "Only one route candidate exists. Ranking unchanged."
                
        # Persist safety report to database
        from app.db.connection import get_db
        try:
            db = await get_db()
            import uuid
            report_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Use midpoints from the target segment if exact location isn't provided
            # We assume for this prototype that the event has some coordinates or we use segment coordinates
            lat = target_segment.start.latitude
            lon = target_segment.start.longitude
            
            await db.execute(
                """
                INSERT INTO safety_reports (id, event_type, severity, latitude, longitude, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                report_id, event.event_type, event.severity, lat, lon, now
            )
        except Exception as e:
            print(f"[DB ERROR] Failed to persist safety report: {e}")
                
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
            reason=reason,
            updated_ranking=new_ranking.model_dump()
        )
