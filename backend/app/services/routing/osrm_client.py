import uuid
import httpx
from datetime import datetime
from fastapi import HTTPException
from app.services.routing.routing_service import RoutingService
from app.schemas.journey import JourneyRequest, JourneyResponse, JourneySegment, Location
from app.schemas.risk import SegmentContext
from app.schemas.ranking import RouteCandidate
from app.core.config import settings
from app.services.risk.risk_service import RiskService
from app.services.routing.route_ranking_service import RouteRankingService

class OSRMRoutingService(RoutingService):
    def __init__(self):
        self.base_url = settings.OSRM_BASE_URL
        self.profile = settings.OSRM_PROFILE
        self.risk_service = RiskService()
        self.ranking_service = RouteRankingService()

    async def get_journey(self, request: JourneyRequest) -> JourneyResponse:
        if request.origin.latitude == request.destination.latitude and \
           request.origin.longitude == request.destination.longitude:
            raise HTTPException(status_code=400, detail="Origin and destination cannot be the same")

        # OSRM expects coordinates in lon,lat format
        coords = f"{request.origin.longitude},{request.origin.latitude};{request.destination.longitude},{request.destination.latitude}"
        # Request alternatives (limit to 3 for prototype)
        url = f"{self.base_url}/route/v1/{self.profile}/{coords}?alternatives=3&steps=true&geometries=geojson&overview=full"

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

        journey_id = str(uuid.uuid4())
        candidates = []

        for route_idx, route in enumerate(data.get("routes", [])):
            legs = route.get("legs", [])
            if not legs:
                continue

            leg = legs[0]
            steps = leg.get("steps", [])

            route_id = str(uuid.uuid4())
            segments = []
            sequence = 1

            for step in steps:
                if step.get("distance", 0) == 0 and not step.get("geometry"):
                    continue

                geometry = step.get("geometry", {})
                if not geometry or geometry.get("type") != "LineString":
                    continue 

                coords_list = geometry.get("coordinates", [])
                if len(coords_list) < 2:
                    continue 

                start_lon, start_lat = coords_list[0]
                end_lon, end_lat = coords_list[-1]

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
                
                # Evaluate segment risk
                context = SegmentContext(departure_time=request.departure_time or datetime.now())
                risk_score = self.risk_service.calculate_risk(segment, context)
                segment.risk_score = risk_score.risk_score
                segment.confidence_score = risk_score.confidence_score
                segment.explanation = risk_score.explanation.model_dump() if risk_score.explanation else None
                
                segments.append(segment)
                sequence += 1

            if not segments:
                continue
                
            metrics = self.ranking_service.aggregate_metrics(segments)
            candidates.append(RouteCandidate(route_id=route_id, metrics=metrics, segments=segments))

        if not candidates:
            raise HTTPException(status_code=404, detail="Could not generate valid journey segments")

        ranking_response = self.ranking_service.rank_routes(journey_id, candidates)
        
        # Primary route is safest (or first candidate if safest is somehow None)
        primary = ranking_response.safest_route
        if not primary:
            # Fallback
            primary = candidates[0]
            primary_dist = primary.metrics.total_distance_m
            primary_dur = primary.metrics.total_duration_s
            primary_segs = primary.segments
        else:
            primary_dist = primary.distance_m
            primary_dur = primary.duration_s
            primary_segs = primary.segments

        return JourneyResponse(
            journey_id=journey_id,
            origin=request.origin,
            destination=request.destination,
            distance_m=primary_dist,
            duration_s=primary_dur,
            segments=primary_segs,
            ranking=ranking_response.model_dump()
        )
