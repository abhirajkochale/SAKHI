import os
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import math

router = APIRouter()

class PlaceResponse(BaseModel):
    name: str
    address: str
    place_id: str
    latitude: float
    longitude: float
    distance_m: int
    business_status: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@router.get("/nearby", response_model=List[PlaceResponse], summary="Find nearby places using Google Places API")
def search_places_nearby(lat: float, lon: float, category: str, radius_m: int = 2000):
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Google API key not configured")

    if category == "washroom":
        included_types = ["restroom"]
    elif category == "police":
        included_types = ["police"]
    elif category == "medical":
        included_types = ["hospital", "medical_clinic", "doctor"]
    else:
        raise HTTPException(status_code=400, detail="Invalid category")

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.id,places.businessStatus,places.rating,places.userRatingCount"
    }

    payload = {
        "includedTypes": included_types,
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lon
                },
                "radius": float(radius_m)
            }
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        places = data.get("places", [])
    except Exception as e:
        print(f"Google Places API error: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch places from Google")

    results = []
    for p in places:
        p_lat = p.get("location", {}).get("latitude", 0)
        p_lon = p.get("location", {}).get("longitude", 0)
        dist = haversine(lat, lon, p_lat, p_lon)

        results.append(PlaceResponse(
            name=p.get("displayName", {}).get("text", "Unknown Place"),
            address=p.get("formattedAddress", "No address provided"),
            place_id=p.get("id", ""),
            latitude=p_lat,
            longitude=p_lon,
            distance_m=int(dist),
            business_status=p.get("businessStatus"),
            rating=p.get("rating"),
            user_ratings_total=p.get("userRatingCount")
        ))
        
    results.sort(key=lambda x: x.distance_m)
    return results
