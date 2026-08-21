from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from app.schemas.journey import Location

class Amenity(BaseModel):
    """
    Pydantic schema representing a normalized amenity (washroom, hospital, etc.)
    with validation logic for coordinates and default fallbacks.
    """
    amenity_id: str = Field(..., description="Unique identifier for the amenity")
    type: str = Field(..., description="Type of amenity (e.g. TOILET, HOSPITAL, PHARMACY)")
    name: str = Field(default="Unknown Facility", description="Name of the facility")
    lat: float = Field(..., description="Latitude coordinate")
    lon: float = Field(..., description="Longitude coordinate")
    is_24_7: bool = Field(default=False, description="Whether the facility is open 24/7")
    source_file: Optional[str] = Field(default=None, description="Original source CSV file")
    source_type: Optional[str] = Field(default=None, description="Source data classification (e.g., REAL, SYNTHETIC)")
    source_date_range: Optional[str] = Field(default=None, description="Validity date range of source data")
    normalization_notes: Optional[str] = Field(default=None, description="Notes on standardizing the record")
    is_stale: bool = Field(default=False, description="Flag indicating if the facility data is outdated or stale")

    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return v

    @field_validator("lon")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return v

class AmenityResponse(Amenity):
    """
    API response schema extending Amenity to include distance from the query point or route.
    """
    distance_m: Optional[float] = Field(default=None, description="Distance from origin/route in meters")

class AlongRouteAmenitiesRequest(BaseModel):
    """
    Request schema for calculating amenities along a specified travel route.
    """
    route_coords: List[Location] = Field(..., description="Ordered list of coordinates representing the route path")
    deviation_distance_m: float = Field(default=200.0, description="Max allowed distance from route in meters to return an amenity")
    type: Optional[str] = Field(default="TOILET", description="Filter by amenity type (e.g., TOILET). If None, returns all.")
