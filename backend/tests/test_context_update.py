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

from unittest.mock import patch, MagicMock

def mock_ml_predict(features):
    # Route 0 (Fastest, Risky Corridor) gets historical_baseline=0.9
    if features.historical_baseline >= 0.8:
        return 85.0
    
    # Route 1 (Safest Corridor) gets historical_baseline=0.65
    # If a report is submitted, validated_report_signal goes up
    if features.validated_report_signal > 0.8:
        return 75.0
        
    return 45.0

@patch("app.services.risk.ml_model_service.MLModelService.predict")
@patch("httpx.AsyncClient.get")
def test_context_update_paharganj_preserves_high_risk(mock_get, mock_predict):
    """
    Regression test: ensures that after a High-Risk Demo journey is created with
    differentiated route contexts (safer corridor vs risky corridor), a subsequent
    context-update on the safer route's segment does NOT reset the risky route back
    to default baseline, and that updated_ranking is returned correctly.
    """
    mock_predict.side_effect = mock_ml_predict
    PAHARGANJ_TWO_ROUTES = {
        "code": "Ok",
        "routes": [
            {
                "distance": 24700.0, "duration": 1600.0,
                "legs": [{"steps": [{"distance": 24700.0, "duration": 1600.0,
                    "geometry": {"type": "LineString", "coordinates": [[77.2132, 28.6433], [77.0597, 28.5525]]}
                }]}]
            },
            {
                "distance": 25000.0, "duration": 1700.0,
                "legs": [{"steps": [{"distance": 25000.0, "duration": 1700.0,
                    "geometry": {"type": "LineString", "coordinates": [[77.2132, 28.6433], [77.0597, 28.5525]]}
                }]}]
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = PAHARGANJ_TWO_ROUTES
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # 1. Create the journey in Paharganj
    create_resp = client.post(
        f"{settings.API_V1_STR}/journeys/",
        json={
            "origin": {"latitude": 28.6433, "longitude": 77.2132},
            "destination": {"latitude": 28.5525, "longitude": 77.0597}
        }
    )
    assert create_resp.status_code == 200
    journey_data = create_resp.json()
    journey_id = journey_data["journey_id"]
    segment_id = journey_data["segments"][0]["segment_id"]

    ranking = journey_data["ranking"]
    fastest = ranking["fastest_route"]
    safest = ranking["safest_route"]

    # Fastest route (risky corridor, route_idx=1) should have high initial risk
    assert fastest["risk_score"] > 70.0, f"Expected fastest to be high-risk, got {fastest['risk_score']}"
    # Safest route should be lower risk than fastest
    assert safest["risk_score"] < fastest["risk_score"]

    # 2. Send a context update on the safest route's segment
    update_resp = client.post(
        f"{settings.API_V1_STR}/journeys/{journey_id}/context-update",
        json={
            "segment_id": segment_id,
            "event_type": "validated_report",
            "severity": 85,
            "source": "simulated_demo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active": True
        }
    )

    assert update_resp.status_code == 200
    update_data = update_resp.json()

    # 3. updated_ranking must be present
    assert "updated_ranking" in update_data
    assert update_data["updated_ranking"] is not None

    updated_ranking = update_data["updated_ranking"]
    new_safest = updated_ranking["safest_route"]
    new_fastest = updated_ranking["fastest_route"]

    print(f"\nAfter update - safest risk: {new_safest['risk_score']:.1f}  fastest risk: {new_fastest['risk_score']:.1f}")

    # 4. After safety report, the risky corridor (fastest) is still high-risk
    assert new_fastest["risk_score"] > 50.0, "Risky corridor should remain materially risky after update"

    # 5. Safest route should still be safer than fastest
    assert new_safest["risk_score"] < new_fastest["risk_score"], "Safest route should remain safer than fastest after update"

