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
