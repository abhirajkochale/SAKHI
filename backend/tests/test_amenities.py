from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_get_nearby_amenities():
    """
    Test successful retrieval of nearby washrooms from the CSV data.
    Origin point near Connaught Place (MCD Public Toilet CP is at 28.632, 77.218).
    """
    response = client.get(
        f"{settings.API_V1_STR}/amenities/nearby",
        params={
            "latitude": 28.630,
            "longitude": 77.215,
            "radius_m": 1000.0,
            "type": "TOILET"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # The closest washroom should be MCD Public Toilet CP
    assert data[0]["name"] == "MCD Public Toilet CP"
    assert data[0]["type"] == "TOILET"
    assert "distance_m" in data[0]
    assert data[0]["is_24_7"] is True
    # Verify coordinates validation works and is_stale is loaded
    assert "is_stale" in data[0]

def test_get_nearby_amenities_validation():
    """
    Test coordinate bounds validation for GET /amenities/nearby.
    """
    # Latitude out of bounds
    response = client.get(
        f"{settings.API_V1_STR}/amenities/nearby",
        params={
            "latitude": 95.0,
            "longitude": 77.215,
            "radius_m": 1000.0,
            "type": "TOILET"
        }
    )
    assert response.status_code == 400
    assert "detail" in response.json()

def test_get_amenities_along_route():
    """
    Test successful retrieval of washrooms within deviation range along a mock route.
    """
    # Mock route path starting near Hauz Khas (28.548, 77.202 is MCD Toilet Hauz Khas)
    route_coords = [
        {"latitude": 28.546, "longitude": 77.200},
        {"latitude": 28.547, "longitude": 77.201},
        {"latitude": 28.548, "longitude": 77.202}, # directly passing Hauz Khas toilet
        {"latitude": 28.549, "longitude": 77.203}
    ]
    
    response = client.post(
        f"{settings.API_V1_STR}/amenities/along-route",
        json={
            "route_coords": route_coords,
            "deviation_distance_m": 150.0,
            "type": "TOILET"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Hauz Khas toilet should be found
    names = [amn["name"] for amn in data]
    assert "MCD Toilet Hauz Khas" in names
    
    # Haversine distance should be very low since we pass directly through it
    hauz_khas_record = [amn for amn in data if amn["name"] == "MCD Toilet Hauz Khas"][0]
    assert hauz_khas_record["distance_m"] < 50.0
    assert hauz_khas_record["is_24_7"] is False
