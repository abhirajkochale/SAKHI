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


@router.get("/nearby", response_model=list[NearestAmenityResponse], summary="Find nearby facilities within radius")
async def find_nearby(lat: float, lon: float, type: str = "police", radius_m: float = 2000.0):
    """Find police stations, hospitals, or washrooms within 2km from real spatial datasets."""
    lookup = get_segment_lookup_service()
    results = []
    
    if type == "police" and not lookup._police.empty:
        df = lookup._police
        name_col = "name" if "name" in df.columns else "district"
        for _, row in df.iterrows():
            d = _haversine(lat, lon, float(row["latitude"]), float(row["longitude"]))
            if d <= radius_m:
                results.append(NearestAmenityResponse(
                    name=str(row.get(name_col, "Police Station")),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    distance_m=round(d),
                    type="Police Station"
                ))
    
    elif type == "hospital" and not lookup._hospitals.empty:
        df = lookup._hospitals
        name_col = "name" if "name" in df.columns else "type"
        for _, row in df.iterrows():
            d = _haversine(lat, lon, float(row["latitude"]), float(row["longitude"]))
            if d <= radius_m:
                results.append(NearestAmenityResponse(
                    name=str(row.get(name_col, "Hospital")),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    distance_m=round(d),
                    type="Hospital"
                ))
    
    elif type == "washroom" and not lookup._amenities.empty:
        df = lookup._amenities
        toilets = df[df["type"].astype(str).str.contains("toilet|Toilet|washroom|Washroom", case=False, na=False)]
        if toilets.empty:
            toilets = df
        for _, row in toilets.iterrows():
            d = _haversine(lat, lon, float(row["latitude"]), float(row["longitude"]))
            if d <= radius_m:
                results.append(NearestAmenityResponse(
                    name=str(row.get("name", "Public Toilet")),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    distance_m=round(d),
                    type="Washroom"
                ))
    
    results.sort(key=lambda x: x.distance_m)
    return results

