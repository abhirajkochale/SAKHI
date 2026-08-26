from fastapi import APIRouter
from app.api.v1.endpoints import amenities, emergency, health, journeys, incidents, washrooms, users, call_friend

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(amenities.router, prefix="/amenities", tags=["amenities"])
api_router.include_router(journeys.router, prefix="/journeys", tags=["journeys"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["emergency"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(washrooms.router, prefix="/washrooms", tags=["washrooms"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(call_friend.router, prefix="/call-friend", tags=["call-friend"])