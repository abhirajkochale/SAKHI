from fastapi import APIRouter, Depends
from app.schemas.journey import JourneyRequest, JourneyResponse
from app.schemas.context import ContextUpdateEvent, ContextUpdateResponse
from app.services.routing.routing_service import RoutingService
from app.services.routing.osrm_client import OSRMRoutingService
from app.services.context_update_service import ContextUpdateService
from app.schemas.emergency import CheckinRequest, CheckinResponse
from app.services.emergency.emergency_service import get_emergency_service

router = APIRouter()

# Dependency to inject the routing service
def get_routing_service() -> RoutingService:
    return OSRMRoutingService()

def get_context_update_service() -> ContextUpdateService:
    return ContextUpdateService()

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

@router.post("/{journey_id}/context-update", response_model=ContextUpdateResponse, summary="Update contextual safety signal for a journey segment")
def update_journey_context(
    journey_id: str,
    event: ContextUpdateEvent,
    context_service: ContextUpdateService = Depends(get_context_update_service)
):
    """
    Simulates a contextual safety event (e.g. validated report) on a segment,
    triggers recalculation of risk and confidence, updates SHAP explanations,
    and recalculates Safest/Balanced/Fastest route ranking.
    """
    return context_service.process_update(journey_id, event)

@router.post("/{journey_id}/checkin", response_model=CheckinResponse, summary="Dead-man's switch check-in")
def check_in_journey(
    journey_id: str,
    request: CheckinRequest,
    emergency_service = Depends(get_emergency_service)
):
    """
    Records a check-in for the dead-man's switch feature. If a check-in is not received
    within the timeout window, an SOS event is automatically triggered.
    """
    return emergency_service.record_checkin(journey_id, request)
