from fastapi import APIRouter
from app.api.v1.endpoints import health, journeys, incidents

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(journeys.router, prefix="/journeys", tags=["journeys"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
