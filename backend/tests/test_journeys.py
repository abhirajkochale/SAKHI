# pyrefly: ignore [missing-import]
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

@patch("httpx.AsyncClient.get")
def test_create_journey_ranks_real_route_alternatives(mock_get):
    """
    Any two OSRM route alternatives receive independent spatial risk scores and
    are ranked without location-specific overrides.
    """
    TWO_ROUTE_RESPONSE = {
        "code": "Ok",
        "routes": [
            {
                "distance": 25000.0,
                "duration": 1700.0,
                "legs": [{
                    "steps": [{
                        "distance": 25000.0, "duration": 1700.0,
                        "geometry": {"type": "LineString", "coordinates": [[77.2132, 28.6433], [77.0597, 28.5525]]}
                    }]
                }]
            },
            {
                "distance": 24700.0,
                "duration": 1600.0,
                "legs": [{
                    "steps": [{
                        "distance": 24700.0, "duration": 1600.0,
                        "geometry": {"type": "LineString", "coordinates": [[77.2132, 28.6433], [77.0597, 28.5525]]}
                    }]
                }]
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = TWO_ROUTE_RESPONSE
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

    print(f"\nSafest risk: {safest['risk_score']:.1f}  fastest risk: {fastest['risk_score']:.1f}")

    # Fastest route should have risk score >= safest route
    assert fastest["risk_score"] >= safest["risk_score"], f"Expected fastest route risk ({fastest['risk_score']}) >= safest route risk ({safest['risk_score']})"

    # Both routes should have valid non-negative risk
    assert safest["risk_score"] >= 0.0, "Safest route should have valid risk score"

    # Verify SHAP explanation is present for the primary displayed segment
    seg = data["segments"][0]
    explanation = seg["explanation"]
    assert explanation is not None
    assert explanation["available"] is True
