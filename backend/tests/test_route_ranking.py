# pyrefly: ignore [missing-import]
import pytest
from app.schemas.journey import JourneySegment, Location
from app.schemas.ranking import RouteCandidate, RouteMetrics
from app.services.routing.route_ranking_service import RouteRankingService
from app.core.config import settings

def make_segment(distance: float, duration: float, risk: float, confidence: float):
    seg = JourneySegment(
        segment_id="s1", journey_id="j1", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0),
        end_location=Location(latitude=0, longitude=0),
        distance_m=distance, duration_s=duration, geometry={"type": "LineString", "coordinates": []}
    )
    seg.risk_score = risk
    seg.confidence_score = confidence
    return seg

def test_aggregate_metrics():
    service = RouteRankingService()
    seg1 = make_segment(100.0, 100.0, 10.0, 100.0)
    seg2 = make_segment(100.0, 200.0, 40.0, 50.0)
    
    metrics = service.aggregate_metrics([seg1, seg2])
    assert metrics.total_distance_m == 200.0
    assert metrics.total_duration_s == 300.0
    # (10*100 + 40*200) / 300 = (1000 + 8000) / 300 = 30.0
    assert metrics.route_risk_score == 30.0
    assert metrics.max_segment_risk == 40.0
    assert metrics.average_confidence == 75.0
    assert metrics.min_confidence == 50.0
    # uncertainty = 1 - 0.75 = 0.25
    assert metrics.uncertainty_penalty == 0.25
    
def test_zero_duration_edge_case():
    service = RouteRankingService()
    seg = make_segment(0.0, 0.0, 50.0, 50.0)
    metrics = service.aggregate_metrics([seg])
    assert metrics.total_duration_s == 0.0
    assert metrics.route_risk_score == 0.0

def test_1_candidate_case():
    service = RouteRankingService()
    seg = make_segment(100.0, 100.0, 10.0, 100.0)
    metrics = service.aggregate_metrics([seg])
    c1 = RouteCandidate(route_id="r1", metrics=metrics, segments=[seg])
    
    resp = service.rank_routes("j1", [c1])
    assert resp.safest_route.route_id == "r1"
    assert resp.balanced_route.route_id == "r1"
    assert resp.fastest_route.route_id == "r1"
    
def test_2_candidate_case():
    service = RouteRankingService()
    segA = make_segment(600.0, 600.0, 20.0, 90.0)
    cA = RouteCandidate(route_id="A", metrics=service.aggregate_metrics([segA]), segments=[segA])
    
    segB = make_segment(400.0, 400.0, 60.0, 90.0)
    cB = RouteCandidate(route_id="B", metrics=service.aggregate_metrics([segB]), segments=[segB])
    
    resp = service.rank_routes("j1", [cA, cB])
    assert resp.safest_route.route_id == "A"
    assert resp.fastest_route.route_id == "B"

def test_3_candidates_case():
    service = RouteRankingService()
    
    # Route A: slow (600), safe (20), conf (90)
    segA = make_segment(600.0, 600.0, 20.0, 90.0)
    metricsA = service.aggregate_metrics([segA])
    cA = RouteCandidate(route_id="A", metrics=metricsA, segments=[segA])

    # Route B: fast (400), risky (60), conf (90)
    segB = make_segment(400.0, 400.0, 60.0, 90.0)
    metricsB = service.aggregate_metrics([segB])
    cB = RouteCandidate(route_id="B", metrics=metricsB, segments=[segB])

    # Route C: balanced (500), med risk (35), conf (90)
    segC = make_segment(500.0, 500.0, 35.0, 90.0)
    metricsC = service.aggregate_metrics([segC])
    cC = RouteCandidate(route_id="C", metrics=metricsC, segments=[segC])
    
    resp = service.rank_routes("j1", [cA, cB, cC])
    
    # SAFEST should pick A because its risk is lowest
    assert resp.safest_route.route_id == "A"
    
    # FASTEST should pick B because its duration is lowest
    assert resp.fastest_route.route_id == "B"
    
    # BALANCED should pick C 
    assert resp.balanced_route.route_id == "C"
    
def test_identical_travel_times():
    # If times are identical, risk should be the decider
    service = RouteRankingService()
    segA = make_segment(100.0, 500.0, 20.0, 90.0)
    segB = make_segment(100.0, 500.0, 60.0, 90.0)
    
    cA = RouteCandidate(route_id="A", metrics=service.aggregate_metrics([segA]), segments=[segA])
    cB = RouteCandidate(route_id="B", metrics=service.aggregate_metrics([segB]), segments=[segB])
    
    resp = service.rank_routes("j1", [cA, cB])
    assert resp.safest_route.route_id == "A"
    assert resp.fastest_route.route_id == "A"  # time is same, tie breaks on risk
    
def test_identical_risks():
    service = RouteRankingService()
    segA = make_segment(100.0, 600.0, 20.0, 90.0)
    segB = make_segment(100.0, 400.0, 20.0, 90.0)
    
    cA = RouteCandidate(route_id="A", metrics=service.aggregate_metrics([segA]), segments=[segA])
    cB = RouteCandidate(route_id="B", metrics=service.aggregate_metrics([segB]), segments=[segB])
    
    resp = service.rank_routes("j1", [cA, cB])
    assert resp.safest_route.route_id == "B"  # risk is same, tie breaks on duration
    assert resp.fastest_route.route_id == "B"
    
def test_identical_confidence():
    service = RouteRankingService()
    segA = make_segment(100.0, 500.0, 20.0, 100.0)
    segB = make_segment(100.0, 500.0, 20.0, 100.0)
    
    cA = RouteCandidate(route_id="A", metrics=service.aggregate_metrics([segA]), segments=[segA])
    cB = RouteCandidate(route_id="B", metrics=service.aggregate_metrics([segB]), segments=[segB])
    
    resp = service.rank_routes("j1", [cA, cB])
    assert resp.safest_route.route_id == "A"
    
def test_deterministic_tie():
    service = RouteRankingService()
    segA = make_segment(100.0, 500.0, 20.0, 90.0)
    segB = make_segment(100.0, 500.0, 20.0, 90.0)
    
    # Tie broken by route_id lexicographically
    cA = RouteCandidate(route_id="A", metrics=service.aggregate_metrics([segA]), segments=[segA])
    cB = RouteCandidate(route_id="B", metrics=service.aggregate_metrics([segB]), segments=[segB])
    
    resp = service.rank_routes("j1", [cB, cA]) # pass in reverse order to ensure it sorts correctly
    assert resp.safest_route.route_id == "A"
    
def test_uncertainty_penalty():
    service = RouteRankingService()
    # Identical time and risk, but B has lower confidence
    segA = make_segment(100.0, 500.0, 20.0, 90.0)
    segB = make_segment(100.0, 500.0, 20.0, 30.0)
    
    cA = RouteCandidate(route_id="A", metrics=service.aggregate_metrics([segA]), segments=[segA])
    cB = RouteCandidate(route_id="B", metrics=service.aggregate_metrics([segB]), segments=[segB])
    
    resp = service.rank_routes("j1", [cA, cB])
    assert resp.safest_route.route_id == "A"
    assert resp.fastest_route.route_id == "A"
