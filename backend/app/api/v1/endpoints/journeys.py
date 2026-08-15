from fastapi import APIRouter, Depends
from app.schemas.journey import JourneyRequest, JourneyResponse
from app.services.routing.routing_service import RoutingService
from app.services.routing.osrm_client import OSRMRoutingService

router = APIRouter()

# Dependency to inject the routing service
def get_routing_service() -> RoutingService:
    return OSRMRoutingService()

@router.post("/", response_model=JourneyResponse, summary="Create a new journey")
async def create_journey(
    request: JourneyRequest,
    routing_service: RoutingService = Depends(get_routing_service)
):
    """
    Creates a new journey by calculating a route between the origin and destination,
    and returns the route divided into actionable JourneySegments.
    """
    return await routing_service.get_journey(request)
