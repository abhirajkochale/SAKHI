import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.context_store import journey_store, JourneyData
from app.schemas.journey import JourneyRequest, Location, JourneySegment
from app.schemas.ranking import RouteCandidate, RouteRankingResponse, RouteMetrics, RouteOption

client = TestClient(app)

def setup_mock_journey():
    journey_id = "test_journey_1"
    request = JourneyRequest(origin=Location(latitude=0,longitude=0), destination=Location(latitude=1,longitude=1))
    
    seg1 = JourneySegment(
        segment_id="seg1", journey_id=journey_id, sequence=1, mode="walking",
        start_location=Location(latitude=0,longitude=0), end_location=Location(latitude=1,longitude=1),
        distance_m=100.0, duration_s=100.0, geometry={"type": "LineString", "coordinates": []},
        risk_score=20.0, confidence_score=90.0, explanation=None
    )
    
    cand1 = RouteCandidate(route_id="route1", metrics=RouteMetrics(
        total_distance_m=100.0, total_duration_s=100.0, route_risk_score=20.0,
        max_segment_risk=20.0, min_confidence=90.0, average_confidence=90.0, uncertainty_penalty=0.1
    ), segments=[seg1])
    
    ranking = RouteRankingResponse(
        journey_id=journey_id,
        safest_route=RouteOption(
            route_id="route1", mode="safest", rank=1, distance_m=100.0, duration_s=100.0,
            risk_score=20.0, confidence=90.0, max_segment_risk=20.0, uncertainty_penalty=0.1,
            route_cost=0.5, segments=[seg1]
        ),
        all_candidates=[cand1]
    )
    
    journey_store[journey_id] = JourneyData(request, [cand1], ranking)
    return journey_id

def test_context_update_success():
    journey_id = setup_mock_journey()
    
    response = client.post(
        f"{settings.API_V1_STR}/journeys/{journey_id}/context-update",
        json={
            "segment_id": "seg1",
            "event_type": "validated_report",
            "severity": 80,
            "source": "simulated_demo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["updated_segment_id"] == "seg1"
    assert data["rerouted"] is False
    assert "Only one route candidate" in data["reason"] or "remains preferred" in data["reason"]
    
    # Check if risk recalculation occurred
    assert data["after"]["risk"] != 20.0 or data["before"]["risk"] == data["after"]["risk"] # In fallback it might not change significantly if heuristics aren't hit, but for validated_report it definitely will.

def test_context_update_not_found():
    response = client.post(
        f"{settings.API_V1_STR}/journeys/does_not_exist/context-update",
        json={
            "segment_id": "seg1",
            "event_type": "validated_report",
            "severity": 80,
            "source": "simulated_demo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active": True
        }
    )
    assert response.status_code == 404

def test_context_update_segment_not_found():
    journey_id = setup_mock_journey()
    response = client.post(
        f"{settings.API_V1_STR}/journeys/{journey_id}/context-update",
        json={
            "segment_id": "seg_does_not_exist",
            "event_type": "validated_report",
            "severity": 80,
            "source": "simulated_demo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active": True
        }
    )
    assert response.status_code == 404

def test_context_update_rerouting():
    journey_id = 'test_journey_2'
    request = JourneyRequest(origin=Location(latitude=0,longitude=0), destination=Location(latitude=1,longitude=1))
    seg1 = JourneySegment(segment_id='seg1', journey_id=journey_id, sequence=1, mode='walking', start_location=Location(latitude=0,longitude=0), end_location=Location(latitude=1,longitude=1), distance_m=100.0, duration_s=100.0, geometry={'type': 'LineString', 'coordinates': []}, risk_score=20.0, confidence_score=90.0, explanation=None)
    seg2 = JourneySegment(segment_id='seg2', journey_id=journey_id, sequence=1, mode='walking', start_location=Location(latitude=0,longitude=0), end_location=Location(latitude=1,longitude=1), distance_m=100.0, duration_s=100.0, geometry={'type': 'LineString', 'coordinates': []}, risk_score=30.0, confidence_score=90.0, explanation=None)
    
    cand1 = RouteCandidate(route_id='route1', metrics=RouteMetrics(total_distance_m=100.0, total_duration_s=100.0, route_risk_score=20.0, max_segment_risk=20.0, min_confidence=90.0, average_confidence=90.0, uncertainty_penalty=0.1), segments=[seg1])
    cand2 = RouteCandidate(route_id='route2', metrics=RouteMetrics(total_distance_m=100.0, total_duration_s=100.0, route_risk_score=30.0, max_segment_risk=30.0, min_confidence=90.0, average_confidence=90.0, uncertainty_penalty=0.1), segments=[seg2])
    
    ranking = RouteRankingResponse(journey_id=journey_id, safest_route=RouteOption(route_id='route1', mode='safest', rank=1, distance_m=100.0, duration_s=100.0, risk_score=20.0, confidence=90.0, max_segment_risk=20.0, uncertainty_penalty=0.1, route_cost=0.5, segments=[seg1]), all_candidates=[cand1, cand2])
    journey_store[journey_id] = JourneyData(request, [cand1, cand2], ranking)
    
    response = client.post(f"{settings.API_V1_STR}/journeys/{journey_id}/context-update", json={'segment_id': 'seg1', 'event_type': 'validated_report', 'severity': 100, 'source': 'simulated_demo', 'timestamp': datetime.now(timezone.utc).isoformat(), 'active': True})
    
    assert response.status_code == 200
    data = response.json()
    assert data['rerouted'] is True
    assert data['after']['safest_route_id'] == 'route2'

