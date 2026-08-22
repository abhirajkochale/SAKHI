import uuid
from typing import List, Optional, Tuple
from app.schemas.journey import JourneySegment
from app.schemas.ranking import RouteCandidate, RouteMetrics, RouteOption, RouteRankingResponse
from app.core.config import settings

class RouteRankingService:
    """
    Ranks alternative routes based on travel time, contextual risk, and uncertainty.
    """
    def __init__(self):
        pass
        
    def aggregate_metrics(self, segments: List[JourneySegment]) -> RouteMetrics:
        if not segments:
            return RouteMetrics(
                total_distance_m=0.0,
                total_duration_s=0.0,
                route_risk_score=0.0,
                max_segment_risk=0.0,
                min_confidence=0.0,
                average_confidence=0.0,
                uncertainty_penalty=0.0
            )
            
        total_dist = sum(s.distance_m for s in segments)
        total_dur = sum(s.duration_s for s in segments)
        
        sum_risk_dur = 0.0
        max_risk = 0.0
        sum_conf = 0.0
        min_conf = 100.0
        
        for s in segments:
            r = s.risk_score if s.risk_score is not None else 0.0
            c = s.confidence_score if s.confidence_score is not None else 0.0
            
            sum_risk_dur += (r * s.duration_s)
            if r > max_risk:
                max_risk = r
                
            sum_conf += c
            if c < min_conf:
                min_conf = c
                
        route_risk = (sum_risk_dur / total_dur) if total_dur > 0 else 0.0
        avg_conf = sum_conf / len(segments)
        
        # Uncertainty penalty = 1 - normalized_confidence
        norm_conf = avg_conf / 100.0
        uncertainty = 1.0 - norm_conf
        
        return RouteMetrics(
            total_distance_m=total_dist,
            total_duration_s=total_dur,
            route_risk_score=route_risk,
            max_segment_risk=max_risk,
            min_confidence=min_conf,
            average_confidence=avg_conf,
            uncertainty_penalty=uncertainty
        )

    def rank_routes(self, journey_id: str, candidates: List[RouteCandidate]) -> RouteRankingResponse:
        if not candidates:
            return RouteRankingResponse(journey_id=journey_id, all_candidates=[])
            
        durations = [c.metrics.total_duration_s for c in candidates]
        risks = [c.metrics.route_risk_score for c in candidates]
        
        min_dur, max_dur = min(durations), max(durations)
        min_risk, max_risk = min(risks), max(risks)
        
        def normalize(val, min_val, max_val):
            if max_val == min_val:
                return 0.0
            return (val - min_val) / (max_val - min_val)
            
        def evaluate_mode(alpha: float, beta: float, gamma: float, mode_name: str) -> Optional[RouteOption]:
            if not candidates:
                return None
            
            scored_candidates = []
            for c in candidates:
                norm_time = normalize(c.metrics.total_duration_s, min_dur, max_dur)
                norm_risk = normalize(c.metrics.route_risk_score, min_risk, max_risk)
                
                cost = alpha * norm_time + beta * norm_risk + gamma * c.metrics.uncertainty_penalty
                scored_candidates.append((cost, c))
                
            # Tie breaking: lower cost -> lower risk -> lower duration -> stable route_id
            scored_candidates.sort(key=lambda x: (
                x[0], 
                x[1].metrics.route_risk_score, 
                x[1].metrics.total_duration_s, 
                x[1].route_id
            ))
            
            best_cost, best_c = scored_candidates[0]
            
            # Inject mock amenity counts based on the route profile
            if mode_name == "safest":
                amenities = {"washrooms": 2, "medical": 1, "police": 2}
            elif mode_name == "fastest":
                amenities = {"washrooms": 0, "medical": 0, "police": 0}
            else: # balanced
                amenities = {"washrooms": 1, "medical": 1, "police": 1}
            
            return RouteOption(
                route_id=best_c.route_id,
                mode=mode_name,
                rank=1,
                distance_m=best_c.metrics.total_distance_m,
                duration_s=best_c.metrics.total_duration_s,
                risk_score=best_c.metrics.route_risk_score,
                confidence=best_c.metrics.average_confidence,
                max_segment_risk=best_c.metrics.max_segment_risk,
                uncertainty_penalty=best_c.metrics.uncertainty_penalty,
                route_cost=best_cost,
                segments=best_c.segments,
                amenity_counts=amenities
            )

        safest = evaluate_mode(settings.RANKING_SAFEST_ALPHA, settings.RANKING_SAFEST_BETA, settings.RANKING_SAFEST_GAMMA, "safest")
        balanced = evaluate_mode(settings.RANKING_BALANCED_ALPHA, settings.RANKING_BALANCED_BETA, settings.RANKING_BALANCED_GAMMA, "balanced")
        fastest = evaluate_mode(settings.RANKING_FASTEST_ALPHA, settings.RANKING_FASTEST_BETA, settings.RANKING_FASTEST_GAMMA, "fastest")

        return RouteRankingResponse(
            journey_id=journey_id,
            safest_route=safest,
            balanced_route=balanced,
            fastest_route=fastest,
            all_candidates=candidates
        )
