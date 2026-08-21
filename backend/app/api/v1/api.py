from fastapi import APIRouter
from app.api.v1.endpoints import health, journeys, emergency, amenities

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(journeys.router, prefix="/journeys", tags=["journeys"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["emergency"])
api_router.include_router(amenities.router, prefix="/amenities", tags=["amenities"])
