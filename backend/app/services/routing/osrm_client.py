import uuid
import httpx
from fastapi import HTTPException
from app.services.routing.routing_service import RoutingService
from app.schemas.journey import JourneyRequest, JourneyResponse, JourneySegment, Location
from app.core.config import settings

class OSRMRoutingService(RoutingService):
    def __init__(self):
        self.base_url = settings.OSRM_BASE_URL
        self.profile = settings.OSRM_PROFILE

    async def get_journey(self, request: JourneyRequest) -> JourneyResponse:
        if request.origin.latitude == request.destination.latitude and \
           request.origin.longitude == request.destination.longitude:
            raise HTTPException(status_code=400, detail="Origin and destination cannot be the same")

        # OSRM expects coordinates in lon,lat format
        coords = f"{request.origin.longitude},{request.origin.latitude};{request.destination.longitude},{request.destination.latitude}"
        url = f"{self.base_url}/route/v1/{self.profile}/{coords}?steps=true&geometries=geojson&overview=full"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise HTTPException(status_code=400, detail="Invalid coordinates or routing profile not supported")
            raise HTTPException(status_code=502, detail="Routing provider returned an error")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Routing provider is unavailable or timed out")

        if data.get("code") != "Ok" or not data.get("routes"):
            raise HTTPException(status_code=404, detail="No route found between the requested locations")

        route = data["routes"][0]
        legs = route.get("legs", [])
        if not legs:
            raise HTTPException(status_code=404, detail="No route found")

        leg = legs[0]
        steps = leg.get("steps", [])

        journey_id = str(uuid.uuid4())
        segments = []
        sequence = 1

        for step in steps:
            # OSRM sometimes returns empty steps for arrivals/departures, skip them if they have 0 distance
            if step.get("distance", 0) == 0 and not step.get("geometry"):
                continue

            # GeoJSON geometry
            geometry = step.get("geometry", {})
            if not geometry or geometry.get("type") != "LineString":
                continue # Need valid linestring geometry

            coords = geometry.get("coordinates", [])
            if len(coords) < 2:
                continue # Need at least start and end

            start_lon, start_lat = coords[0]
            end_lon, end_lat = coords[-1]

            segment = JourneySegment(
                segment_id=str(uuid.uuid4()),
                journey_id=journey_id,
                sequence=sequence,
                mode="walking" if self.profile == "foot" else self.profile,
                start_location=Location(latitude=start_lat, longitude=start_lon),
                end_location=Location(latitude=end_lat, longitude=end_lon),
                distance_m=step.get("distance", 0.0),
                duration_s=step.get("duration", 0.0),
                geometry=geometry
            )
            segments.append(segment)
            sequence += 1

        if not segments:
            raise HTTPException(status_code=404, detail="Could not generate valid journey segments")

        return JourneyResponse(
            journey_id=journey_id,
            origin=request.origin,
            destination=request.destination,
            distance_m=route.get("distance", 0.0),
            duration_s=route.get("duration", 0.0),
            segments=segments
        )
