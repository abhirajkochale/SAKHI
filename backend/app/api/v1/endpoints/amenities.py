from fastapi import APIRouter
from pydantic import BaseModel
import math

from app.services.risk.segment_lookup_service import get_segment_lookup_service

router = APIRouter()


class PublicToilet(BaseModel):
    id: str
    name: str
    type: str
    address: str
    district: str
    latitude: float
    longitude: float


class NearestAmenityResponse(BaseModel):
    name: str
    latitude: float
    longitude: float
    distance_m: int
    type: str


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371e3
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


@router.get("/public-toilets", response_model=list[PublicToilet], summary="List public toilet locations")
async def list_public_toilets():
    """Expose verified public toilet/washroom coordinates for the mobile map."""
    return await get_segment_lookup_service().get_public_toilets()


@router.get("/nearest", response_model=NearestAmenityResponse, summary="Find nearest facility")
async def find_nearest(lat: float, lon: float, type: str = "police"):
    """Find nearest police station, hospital, or washroom from real spatial datasets."""
    lookup = get_segment_lookup_service()
    
    if type == "police" and not lookup._police.empty:
        df = lookup._police
        name_col = "name" if "name" in df.columns else "district"
        best_name, best_lat, best_lon, best_dist = "", 0.0, 0.0, float("inf")
        for _, row in df.iterrows():
            d = _haversine(lat, lon, float(row["latitude"]), float(row["longitude"]))
            if d < best_dist:
                best_dist = d
                best_lat = float(row["latitude"])
                best_lon = float(row["longitude"])
                best_name = str(row.get(name_col, "Police Station"))
        return NearestAmenityResponse(name=best_name, latitude=best_lat, longitude=best_lon, distance_m=round(best_dist), type="Police Station")
    
    elif type == "hospital" and not lookup._hospitals.empty:
        df = lookup._hospitals
        name_col = "name" if "name" in df.columns else "type"
        best_name, best_lat, best_lon, best_dist = "", 0.0, 0.0, float("inf")
        for _, row in df.iterrows():
            d = _haversine(lat, lon, float(row["latitude"]), float(row["longitude"]))
            if d < best_dist:
                best_dist = d
                best_lat = float(row["latitude"])
                best_lon = float(row["longitude"])
                best_name = str(row.get(name_col, "Hospital"))
        return NearestAmenityResponse(name=best_name, latitude=best_lat, longitude=best_lon, distance_m=round(best_dist), type="Hospital")
    
    elif type == "washroom" and not lookup._amenities.empty:
        df = lookup._amenities
        toilets = df[df["type"].astype(str).str.contains("toilet|Toilet|washroom|Washroom", case=False, na=False)]
        if toilets.empty:
            toilets = df
        best_name, best_lat, best_lon, best_dist = "", 0.0, 0.0, float("inf")
        for _, row in toilets.iterrows():
            d = _haversine(lat, lon, float(row["latitude"]), float(row["longitude"]))
            if d < best_dist:
                best_dist = d
                best_lat = float(row["latitude"])
                best_lon = float(row["longitude"])
                best_name = str(row.get("name", "Public Toilet"))
        return NearestAmenityResponse(name=best_name, latitude=best_lat, longitude=best_lon, distance_m=round(best_dist), type="Washroom")
    
    # Fallback
    return NearestAmenityResponse(name="No facility found", latitude=lat, longitude=lon, distance_m=0, type=type)

