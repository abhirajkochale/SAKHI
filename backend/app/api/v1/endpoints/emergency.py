from fastapi import APIRouter, Depends
from app.schemas.emergency import SOSRequest, SOSResponse
from app.services.emergency.emergency_service import EmergencyService, get_emergency_service

router = APIRouter()

@router.post("/sos", response_model=SOSResponse, summary="Trigger SOS Event")
async def trigger_sos(
    request: SOSRequest,
    emergency_service: EmergencyService = Depends(get_emergency_service)
):
    """
    Triggers an SOS event. For the prototype, this stores the event in memory 
    and returns a success response, rather than contacting real emergency services.
    """
    return await emergency_service.trigger_sos(request)
