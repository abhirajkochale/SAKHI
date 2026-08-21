import os
import csv
import math
import logging
from typing import List, Optional
from app.schemas.amenity import Amenity, AmenityResponse
from app.schemas.journey import Location

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes the Haversine distance between two sets of GPS coordinates in meters.
    """
    R = 6371000.0  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def is_date_range_stale(date_range: str, current_year: int = 2026) -> bool:
    """
    Evaluates the source date range to flag stale or outdated data.
    E.g. if the latest year in '2024-2025' is less than (current_year - 1), it is marked stale.
    """
    if not date_range or str(date_range).strip().lower() in ("nan", ""):
        return True  # Treat unverified dates as stale
    
    import re
    # Extract 4-digit years from the date range string (e.g. '2024-2025')
    years = [int(y) for y in re.findall(r"\b\d{4}\b", str(date_range))]
    if not years:
        return True
    
    # Check if the most recent year is older than current_year - 1
    return max(years) < (current_year - 1)

class AmenityService:
    _instance = None
    _amenities: List[Amenity] = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AmenityService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization if already loaded
        if not self._amenities:
            self.load_amenities()

    def load_amenities(self):
        """
        Loads and parses delhi_amenities_normalized.csv on server start.
        Validates GPS coordinates and handles missing/stale information.
        """
        # Formulate robust relative path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.normpath(os.path.join(current_dir, "..", "data", "delhi_amenities_normalized.csv"))
        
        logger.info(f"Loading SAKHI amenities from path: {csv_path}")
        
        if not os.path.exists(csv_path):
            logger.error(f"Amenities CSV file not found at: {csv_path}")
            self._amenities = []
            return

        loaded_amenities = []
        try:
            with open(csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row_idx, row in enumerate(reader):
                    try:
                        # Extract and validate coordinates
                        lat_raw = row.get("lat")
                        lon_raw = row.get("lon")
                        if not lat_raw or not lon_raw:
                            logger.warning(f"Skipping row {row_idx}: Missing latitude or longitude.")
                            continue
                        
                        lat = float(lat_raw)
                        lon = float(lon_raw)

                        # Skip clearly invalid coordinate values
                        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
                            logger.warning(f"Skipping row {row_idx}: GPS coordinates out of bounds ({lat}, {lon}).")
                            continue

                        # Extract name and set fallbacks
                        name = row.get("name", "").strip()
                        if not name or name.lower() in ("nan", ""):
                            amenity_type = row.get("type", "TOILET").upper()
                            name = f"Unnamed {amenity_type.capitalize()}"

                        # Parse boolean values
                        is_24_7_str = row.get("is_24_7", "").strip().lower()
                        is_24_7 = is_24_7_str in ("true", "1", "yes")

                        # Determine staleness flag based on the date range
                        date_range = row.get("source_date_range", "").strip()
                        is_stale = is_date_range_stale(date_range)

                        # Create typed Amenity
                        amenity = Amenity(
                            amenity_id=row.get("amenity_id", f"AMN_GEN_{row_idx}"),
                            type=row.get("type", "TOILET").upper(),
                            name=name,
                            lat=lat,
                            lon=lon,
                            is_24_7=is_24_7,
                            source_file=row.get("source_file"),
                            source_type=row.get("source_type"),
                            source_date_range=date_range,
                            normalization_notes=row.get("normalization_notes"),
                            is_stale=is_stale
                        )
                        loaded_amenities.append(amenity)
                    except ValueError as ve:
                        logger.warning(f"Skipping row {row_idx} due to parsing error: {ve}")
                    except Exception as e:
                        logger.warning(f"Error parsing row {row_idx}: {e}")
            
            self._amenities = loaded_amenities
            logger.info(f"Successfully loaded {len(self._amenities)} amenities from CSV.")
        except Exception as e:
            logger.critical(f"Failed to load amenities CSV: {e}")
            self._amenities = []

    def get_all(self) -> List[Amenity]:
        return self._amenities

    def get_nearby(self, latitude: float, longitude: float, radius_m: float, amenity_type: Optional[str] = "TOILET") -> List[AmenityResponse]:
        """
        Retrieves amenities of a specific type within a given radius using Haversine distance,
        sorted by proximity.
        """
        results: List[AmenityResponse] = []
        for amn in self._amenities:
            # Filter by type if specified
            if amenity_type and amn.type != amenity_type.upper():
                continue
            
            dist = haversine_distance(latitude, longitude, amn.lat, amn.lon)
            if dist <= radius_m:
                results.append(AmenityResponse(
                    **amn.model_dump(),
                    distance_m=round(dist, 1)
                ))
        
        # Sort by distance ascending
        results.sort(key=lambda x: x.distance_m or 0)
        return results

    def get_along_route(self, route_coords: List[Location], deviation_distance_m: float, amenity_type: Optional[str] = "TOILET") -> List[AmenityResponse]:
        """
        Retrieves washrooms/amenities that lie within a deviation threshold of any coordinate point
        on a given travel path.
        """
        results: List[AmenityResponse] = []
        if not route_coords:
            return results

        for amn in self._amenities:
            # Filter by type if specified
            if amenity_type and amn.type != amenity_type.upper():
                continue

            # Calculate the minimum distance to any point along the route
            min_dist = float('inf')
            for pt in route_coords:
                dist = haversine_distance(pt.latitude, pt.longitude, amn.lat, amn.lon)
                if dist < min_dist:
                    min_dist = dist

            # If the closest point is within the deviation threshold, return this amenity
            if min_dist <= deviation_distance_m:
                results.append(AmenityResponse(
                    **amn.model_dump(),
                    distance_m=round(min_dist, 1)
                ))

        # Sort by proximity to route
        results.sort(key=lambda x: x.distance_m or 0)
        return results

# Dependency provider
def get_amenity_service() -> AmenityService:
    return AmenityService()
