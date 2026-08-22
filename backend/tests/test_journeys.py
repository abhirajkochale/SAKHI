import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import httpx
from app.main import app
from app.core.config import settings

client = TestClient(app)

# Fake OSRM JSON response
FAKE_OSRM_RESPONSE = {
    "code": "Ok",
    "routes": [
        {
            "distance": 150.5,
            "duration": 120.0,
            "legs": [
                {
                    "steps": [
                        {
                            "distance": 100.0,
                            "duration": 80.0,
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [
                                    [72.827, 18.922],
                                    [72.828, 18.923]
                                ]
                            }
                        },
                        {
                            "distance": 50.5,
                            "duration": 40.0,
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [
                                    [72.828, 18.923],
                                    [72.829, 18.924]
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    ]
}

from unittest.mock import AsyncMock, MagicMock, patch

@patch("httpx.AsyncClient.get")
def test_create_journey_success(mock_get):
    # Mock httpx response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = FAKE_OSRM_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    response = client.post(
        f"{settings.API_V1_STR}/journeys/",
        json={
            "origin": {"latitude": 18.922, "longitude": 72.827},
            "destination": {"latitude": 18.924, "longitude": 72.829}
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "journey_id" in data
    assert data["distance_m"] == 150.5
    assert data["duration_s"] == 120.0
    assert len(data["segments"]) == 2

    # Check segment 1
    seg1 = data["segments"][0]
    assert seg1["sequence"] == 1
    assert seg1["distance_m"] == 100.0
    assert seg1["start_location"]["latitude"] == 18.922
    assert seg1["end_location"]["latitude"] == 18.923

    # Check segment 2
    seg2 = data["segments"][1]
    assert seg2["sequence"] == 2
    assert seg2["mode"] == "walking"

def test_create_journey_same_coordinates():
    response = client.post(
        f"{settings.API_V1_STR}/journeys/",
        json={
            "origin": {"latitude": 18.922, "longitude": 72.827},
            "destination": {"latitude": 18.922, "longitude": 72.827}
        }
    )
    assert response.status_code == 400
    assert "cannot be the same" in response.json()["detail"].lower()

@patch("httpx.AsyncClient.get")
def test_create_journey_no_route(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"code": "NoRoute"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    response = client.post(
        f"{settings.API_V1_STR}/journeys/",
        json={
            "origin": {"latitude": 18.922, "longitude": 72.827},
            "destination": {"latitude": 18.924, "longitude": 72.829}
        }
    )
    assert response.status_code == 404

@patch("httpx.AsyncClient.get")
def test_create_journey_provider_timeout(mock_get):
    mock_get.side_effect = httpx.RequestError("Timeout")

    response = client.post(
        f"{settings.API_V1_STR}/journeys/",
        json={
            "origin": {"latitude": 18.922, "longitude": 72.827},
            "destination": {"latitude": 18.924, "longitude": 72.829}
        }
    )
    assert response.status_code == 503

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
def test_create_journey_paharganj_demo(mock_get, mock_predict):
    """
    Paharganj High-Risk Demo:
    With 2 OSRM route alternatives:
      - route_idx=0 (safer corridor): moderate synthetic signals -> lower risk
      - route_idx=1 (risky corridor): full high-risk synthetic signals -> high risk
    The ranking service should pick route_idx=0 as 'safest'.
    The 'fastest' route (shorter time) should be route_idx=1 with higher risk.
    """
    mock_predict.side_effect = mock_ml_predict
    PAHARGANJ_TWO_ROUTES = {
        "code": "Ok",
        "routes": [
            {
                "distance": 24700.0,
                "duration": 1600.0,
                "legs": [{
                    "steps": [{
                        "distance": 24700.0, "duration": 1600.0,
                        "geometry": {"type": "LineString", "coordinates": [[77.2132, 28.6433], [77.0597, 28.5525]]}
                    }]
                }]
            },
            {
                "distance": 25000.0,
                "duration": 1700.0,
                "legs": [{
                    "steps": [{
                        "distance": 25000.0, "duration": 1700.0,
                        "geometry": {"type": "LineString", "coordinates": [[77.2132, 28.6433], [77.0597, 28.5525]]}
                    }]
                }]
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = PAHARGANJ_TWO_ROUTES
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    response = client.post(
        f"{settings.API_V1_STR}/journeys/",
        json={
            "origin": {"latitude": 28.6433, "longitude": 77.2132},
            "destination": {"latitude": 28.5525, "longitude": 77.0597}
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["segments"]) > 0

    ranking = data["ranking"]
    assert ranking is not None

    safest = ranking["safest_route"]
    fastest = ranking["fastest_route"]

    assert safest is not None
    assert fastest is not None

    print(f"\nPAHARGANJ safest risk: {safest['risk_score']:.1f}  fastest risk: {fastest['risk_score']:.1f}")

    # Fastest route (route_idx=1, high-risk corridor) should have high risk
    assert fastest["risk_score"] > 70.0, f"Expected fastest route to be high-risk, got {fastest['risk_score']}"

    # Safest route (route_idx=0, safer corridor) should be materially lower than fastest
    assert safest["risk_score"] < fastest["risk_score"], "Safest route should have lower risk than fastest"

    # Both routes should still have elevated risk (Paharganj is a high-risk area)
    assert safest["risk_score"] > 20.0, "Safest route should still have some elevated risk"

    # Verify SHAP explanation is present for the primary displayed segment
    seg = data["segments"][0]
    explanation = seg["explanation"]
    assert explanation is not None
    assert explanation["available"] is True
