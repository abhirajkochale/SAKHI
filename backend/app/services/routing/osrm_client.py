"""
OSRMRoutingService
==================
Calls the public OSRM routing API to get route candidates, then:
1. Builds JourneySegments from OSRM steps
2. Enriches each segment with real spatial context (SegmentLookupService)
3. Calculates contextual risk via RiskService (sakhi XGBoost or heuristic)
4. Aggregates segment metrics and ranks routes (Safest/Balanced/Fastest)

All journeys use fully spatial data from the processed Delhi dataset:
- Police/hospital/amenity distances: computed from real GPS coordinates
- District historical baseline: real NCRB data at district level
- Lighting/CCTV/mobility: nearest synthetic proxy from the processed dataset
"""

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
from app.services.context_store import journey_store, JourneyData
from app.services.risk.segment_lookup_service import get_segment_lookup_service


def _build_real_segment_context(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float,
    departure_time: datetime,
    distance_m: float, duration_s: float,
) -> SegmentContext:
    """
    Build a SegmentContext for any arbitrary segment using real spatial data:
    - District determined via nearest police station
    - Real infrastructure distances
    - Nearest synthetic proxy values (lighting, CCTV, mobility, hotspot)

    This replaces the old hardcoded demo-only context.
    """
    lat = (start_lat + end_lat) / 2.0
    lon = (start_lon + end_lon) / 2.0

    lookup = get_segment_lookup_service()

    # Determine district (via nearest police station — approximation)
    district = lookup.get_district(lat, lon)

    # District historical baseline stats (real NCRB data)
    dist_stats = lookup.get_district_baseline(district)

    # Real infrastructure distances
    infra = lookup.get_infrastructure_distances(lat, lon)

    # Synthetic proxy values (nearest lighting/CCTV/mobility/hotspot segment)
    proxies = lookup.get_synthetic_proxies(lat, lon)

    # Nearest reference segment distance (for confidence)
    _, ref_dist = lookup.get_nearest_reference_segment(lat, lon)

    return SegmentContext(
        departure_time=departure_time,
        segment_lat=lat,
        segment_lon=lon,
        district=district,
        # Historical district context (real NCRB data)
        historical_baseline=dist_stats.get("historical_baseline"),
        cases_per_100k=dist_stats.get("cases_per_100k"),
        severity_weighted_cases_per_100k=dist_stats.get("severity_weighted_cases_per_100k"),
        recent_cases_per_100k=dist_stats.get("recent_cases_per_100k"),
        recent_severity_per_100k=dist_stats.get("recent_severity_per_100k"),
        crime_trend_slope=dist_stats.get("crime_trend_slope"),
        # Road characteristics
        distance_m=distance_m,
        estimated_travel_time_s=duration_s,
        # Synthetic proxies
        lighting_score=proxies.get("lighting_score"),
        cctv_coverage_score=proxies.get("cctv_coverage_score"),
        footfall_proxy=proxies.get("footfall_proxy"),
        nearest_hotspot_distance_m=proxies.get("nearest_hotspot_distance_m"),
        nearest_hotspot_intensity=proxies.get("nearest_hotspot_intensity"),
        # Infrastructure (real GPS-computed)
        distance_to_police_m=infra.get("distance_to_police_m"),
        distance_to_hospital_m=infra.get("distance_to_hospital_m"),
        distance_to_medical_facility_m=infra.get("distance_to_medical_facility_m"),
        distance_to_public_toilet_m=infra.get("distance_to_public_toilet_m"),
        distance_to_nearest_amenity_m=infra.get("distance_to_nearest_amenity_m"),
        # Provenance
        lighting_data_synthetic=True,
        cctv_data_synthetic=True,
        mobility_data_synthetic=True,
        hotspot_data_synthetic=True,
        infrastructure_distances_real=True,
        district_baseline_real=True,
        nearest_segment_distance_m=ref_dist if ref_dist != float("inf") else None,
    )


class OSRMRoutingService(RoutingService):
    """Routes journeys via OSRM and applies the SAKHI contextual risk pipeline."""

    def __init__(self):
        self.base_url = settings.OSRM_BASE_URL
        self.profile = settings.OSRM_PROFILE
        self.risk_service = RiskService()
        self.ranking_service = RouteRankingService()

    async def get_journey(self, request: JourneyRequest) -> JourneyResponse:
        if (request.origin.latitude == request.destination.latitude and
                request.origin.longitude == request.destination.longitude):
            raise HTTPException(status_code=400, detail="Origin and destination cannot be the same")

        coords = (
            f"{request.origin.longitude},{request.origin.latitude};"
            f"{request.destination.longitude},{request.destination.latitude}"
        )
        url = (
            f"{self.base_url}/route/v1/{self.profile}/{coords}"
            f"?alternatives=3&steps=true&geometries=geojson&overview=full"
        )

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

        routes = data.get("routes", [])
        journey_id = str(uuid.uuid4())
        departure = request.departure_time or datetime.now()
        candidates = []
        segment_contexts = {}

        for route_idx, route in enumerate(routes):
            legs = route.get("legs", [])
            if not legs:
                continue

            leg = legs[0]
            steps = leg.get("steps", [])
            route_id = str(uuid.uuid4())
            segments = []
            sequence = 1

            for step in steps:
                if step.get("distance", 0) == 0:
                    continue
                geometry = step.get("geometry", {})
                if not geometry or geometry.get("type") != "LineString":
                    continue
                coords_list = geometry.get("coordinates", [])
                if len(coords_list) < 2:
                    continue

                start_lon, start_lat = coords_list[0]
                end_lon, end_lat = coords_list[-1]
                dist = float(step.get("distance", 0.0))
                dur = float(step.get("duration", 0.0))

                segment = JourneySegment(
                    segment_id=str(uuid.uuid4()),
                    journey_id=journey_id,
                    sequence=sequence,
                    mode="walking" if self.profile == "foot" else self.profile,
                    start_location=Location(latitude=start_lat, longitude=start_lon),
                    end_location=Location(latitude=end_lat, longitude=end_lon),
                    distance_m=dist,
                    duration_s=dur,
                    geometry=geometry,
                )

                # Build context from real spatial data
                context = _build_real_segment_context(
                    start_lat, start_lon, end_lat, end_lon,
                    departure, dist, dur,
                )

                risk_score = self.risk_service.calculate_risk(segment, context)
                segment.risk_score = risk_score.risk_score
                segment.confidence_score = risk_score.confidence_score
                segment.explanation = (
                    risk_score.explanation.model_dump() if risk_score.explanation else None
                )

                segment_contexts[segment.segment_id] = context
                segments.append(segment)
                sequence += 1

            if not segments:
                continue

            metrics = self.ranking_service.aggregate_metrics(segments)
            # Add a small penalty based on distance/duration to break ties between nearly identical routes
            tie_breaker = (metrics.total_distance_m / 10000.0) + (metrics.total_duration_s / 10000.0)
            metrics.route_risk_score = min(100.0, metrics.route_risk_score + tie_breaker)
            candidates.append(RouteCandidate(route_id=route_id, metrics=metrics, segments=segments))

        if not candidates:
            raise HTTPException(status_code=404, detail="Could not generate valid journey segments")

        ranking_response = self.ranking_service.rank_routes(journey_id, candidates)

        # Primary display: safest route segments
        primary = ranking_response.safest_route
        if primary:
            primary_dist = primary.distance_m
            primary_dur = primary.duration_s
            primary_segs = primary.segments
        else:
            first = candidates[0]
            primary_dist = first.metrics.total_distance_m
            primary_dur = first.metrics.total_duration_s
            primary_segs = first.segments

        journey_store[journey_id] = JourneyData(
            request=request,
            candidates=candidates,
            ranking=ranking_response,
            segment_contexts=segment_contexts,
        )

        return JourneyResponse(
            journey_id=journey_id,
            origin=request.origin,
            destination=request.destination,
            distance_m=primary_dist,
            duration_s=primary_dur,
            segments=primary_segs,
            ranking=ranking_response.model_dump(),
        )
