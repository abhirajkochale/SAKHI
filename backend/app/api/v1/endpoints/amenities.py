from fastapi import APIRouter
from pydantic import BaseModel

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


@router.get("/public-toilets", response_model=list[PublicToilet], summary="List public toilet locations")
async def list_public_toilets():
    """Expose verified public toilet/washroom coordinates for the mobile map."""
    return await get_segment_lookup_service().get_public_toilets()
