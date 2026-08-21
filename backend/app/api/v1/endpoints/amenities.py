from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from app.schemas.amenity import AmenityResponse, AlongRouteAmenitiesRequest
from app.services.amenity_service import AmenityService, get_amenity_service

router = APIRouter()

@router.get("/nearby", response_model=List[AmenityResponse], summary="Fetch nearby washrooms or other facilities")
def get_nearby_amenities(
    latitude: float = Query(..., description="Latitude of query origin point"),
    longitude: float = Query(..., description="Longitude of query origin point"),
    radius_m: float = Query(1000.0, description="Search radius in meters", ge=0.0),
    type: Optional[str] = Query("TOILET", description="Filter by facility type (e.g. TOILET, HOSPITAL, PHARMACY)"),
    amenity_service: AmenityService = Depends(get_amenity_service)
):
    """
    Fetches amenities within a specified radius of a given (latitude, longitude) coordinate point.
    By default, it filters to show washrooms (TOILET).
    """
    try:
        # Validate GPS coordinate ranges
        if not (-90.0 <= latitude <= 90.0):
            raise HTTPException(status_code=400, detail="Latitude must be between -90.0 and 90.0")
        if not (-180.0 <= longitude <= 180.0):
            raise HTTPException(status_code=400, detail="Longitude must be between -180.0 and 180.0")
        
        # Clean type input
        amenity_type = type.strip().upper() if type else None
        
        return amenity_service.get_nearby(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            amenity_type=amenity_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch nearby amenities: {str(e)}")

@router.post("/along-route", response_model=List[AmenityResponse], summary="Fetch washrooms or facilities along a route")
def get_amenities_along_route(
    request: AlongRouteAmenitiesRequest,
    amenity_service: AmenityService = Depends(get_amenity_service)
):
    """
    Accepts an ordered array of route coordinates and returns washrooms or facilities that fall
    within a short deviation distance of that route.
    """
    try:
        # Clean type input
        amenity_type = request.type.strip().upper() if request.type else None
        
        return amenity_service.get_along_route(
            route_coords=request.route_coords,
            deviation_distance_m=request.deviation_distance_m,
            amenity_type=amenity_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch amenities along route: {str(e)}")
