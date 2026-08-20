from fastapi import APIRouter
from app.api.v1.endpoints import health, journeys, emergency

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(journeys.router, prefix="/journeys", tags=["journeys"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["emergency"])
