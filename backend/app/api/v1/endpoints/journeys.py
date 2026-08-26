from fastapi import APIRouter, Depends
from app.schemas.journey import JourneyRequest, JourneyResponse
from app.schemas.context import ContextUpdateEvent, ContextUpdateResponse
from app.services.routing.routing_service import RoutingService
from app.services.routing.osrm_client import OSRMRoutingService
from app.services.context_update_service import ContextUpdateService

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
    journey = await routing_service.get_journey(request)
    
    # Persist the active journey in the database
    from app.db.connection import get_db
    try:
        db = await get_db()
        await db.execute(
            """
            INSERT INTO active_journeys (id, origin_lat, origin_lon, dest_lat, dest_lon, status)
            VALUES ($1, $2, $3, $4, $5, 'active')
            """,
            journey.journey_id, request.origin.latitude, request.origin.longitude,
            request.destination.latitude, request.destination.longitude
        )
    except Exception as e:
        print(f"[DB ERROR] Failed to persist active journey {journey.journey_id}: {e}")
        
    return journey

@router.post("/{journey_id}/context-update", response_model=ContextUpdateResponse, summary="Update contextual safety signal for a journey segment")
async def update_journey_context(
    journey_id: str,
    event: ContextUpdateEvent,
    context_service: ContextUpdateService = Depends(get_context_update_service)
):
    """
    Simulates a contextual safety event (e.g. validated report) on a segment,
    triggers recalculation of risk and confidence, updates SHAP explanations,
    and recalculates Safest/Balanced/Fastest route ranking.
    """
    return await context_service.process_update(journey_id, event)

