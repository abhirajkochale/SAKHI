"""
SAKHI Amenity Discovery — Geoapify Places API backend

Provider: Geoapify (https://www.geoapify.com/places-api/)
Data source: OpenStreetMap (processed by Geoapify)
Cost: Free tier — 3,000 req/day, 5 req/sec, no credit card required

The API key (GEOAPIFY_API_KEY) is backend-only.
It must NEVER be exposed to mobile clients, logs, or API responses.

Mobile-facing endpoint (unchanged):
  GET /api/v1/osm-amenities/nearby?lat=&lon=&category=&radius_m=
"""

import math
import logging
from typing import List, Optional
from collections import Counter

import httpx
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_db
from app.models.washroom import Washroom, WashroomFeedback

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Geoapify category mappings ────────────────────────────────────────────────
# Verified in docs/AMENITY_PROVIDER_COMPARISON.md
CATEGORY_MAP: dict = {
    "washroom": {
        "geoapify_categories": "amenity.toilet",
        "default_name": "Public Toilet",
    },
    "police": {
        "geoapify_categories": "service.police",
        "default_name": "Police Station",
    },
    "medical": {
        # healthcare.clinic_or_praxis covers OSM amenity=clinic & amenity=doctors
        "geoapify_categories": "healthcare.hospital,healthcare.clinic_or_praxis",
        "default_name": "Medical Facility",
    },
}

GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"

HTTPX_TIMEOUT = httpx.Timeout(connect=8.0, read=15.0, write=5.0, pool=5.0)


# ── Helpers ───────────────────────────────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371e3
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _normalize_feature(feature: dict, category: str, default_name: str,
                        origin_lat: float, origin_lon: float) -> Optional[dict]:
    """Convert a single Geoapify GeoJSON Feature into a SAKHI amenity dict."""
    try:
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates")  # GeoJSON: [lon, lat]
        if not coords or len(coords) < 2:
            return None

        feat_lon, feat_lat = float(coords[0]), float(coords[1])
        dist = haversine(origin_lat, origin_lon, feat_lat, feat_lon)

        props = feature.get("properties") or {}

        # ── Name Priority Logic ──
        # 1. Explicit name from OSM
        # 2. Brand or Operator if name is missing (common for toilets like Sulabh)
        # 3. Fallback to default_name + street context
        explicit_name = props.get("name")
        brand = props.get("brand")
        operator = props.get("operator")
        street = props.get("street", "")

        if explicit_name:
            name = explicit_name
        elif brand:
            name = brand
        elif operator:
            name = operator
        else:
            # It's an unnamed facility. Don't use raw 'address_line1' as the name.
            if street:
                name = f"{default_name} — {street}"
            else:
                name = default_name

        # ── Address Construction ──
        address_parts = []
        housenumber = props.get("housenumber", "")
        
        # Only add street to address if we didn't just use it in the name
        # Actually, it's fine to have it in the address too for completeness.
        if housenumber and street:
            address_parts.append(f"{housenumber} {street}")
        elif street:
            address_parts.append(street)
            
        suburb = props.get("suburb") or props.get("neighbourhood") or props.get("district", "")
        if suburb:
            address_parts.append(suburb)
            
        city = props.get("city", "")
        if city:
            address_parts.append(city)
            
        address = ", ".join(p for p in address_parts if p) or props.get("address_line2") or None

        phone: Optional[str] = (
            props.get("phone")
            or props.get("contact_phone")
            or props.get("contact_mobile")
        )

        return {
            "id": props.get("place_id") or props.get("osm_id") or "",
            "name": name,
            "category": category,
            "latitude": feat_lat,
            "longitude": feat_lon,
            "address": address,
            "distance_m": int(dist),
            "opening_hours": props.get("opening_hours"),
            "phone": phone,
            "source": "Geoapify / OpenStreetMap",
        }
    except Exception as e:
        logger.warning(f"[Geoapify] Skipped malformed feature: {e}")
        return None


# ── Geoapify HTTP client ──────────────────────────────────────────────────────

async def fetch_from_geoapify(lat: float, lon: float,
                               categories: str, radius_m: int) -> list:
    api_key = settings.GEOAPIFY_API_KEY
    if not api_key:
        logger.error("[Geoapify] GEOAPIFY_API_KEY is not set in backend environment")
        raise HTTPException(
            status_code=500,
            detail=(
                "Amenity discovery is not configured. "
                "Set GEOAPIFY_API_KEY in the backend .env file. "
                "Register free at https://myprojects.geoapify.com/"
            ),
        )

    params = {
        "categories": categories,
        "filter": f"circle:{lon},{lat},{radius_m}",
        "bias": f"proximity:{lon},{lat}",
        "limit": 50,
        "lang": "en",
        "apiKey": api_key,
    }

    logger.info(
        f"[Geoapify] categories={categories!r} within {radius_m}m of ({lat},{lon})"
    )

    try:
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
            response = await client.get(GEOAPIFY_PLACES_URL, params=params)

            if response.status_code == 401:
                logger.error("[Geoapify] HTTP 401 — API key invalid or expired")
                raise HTTPException(
                    status_code=500,
                    detail="Geoapify API key is invalid. Check GEOAPIFY_API_KEY in backend .env.",
                )
            if response.status_code == 429:
                logger.warning("[Geoapify] HTTP 429 — rate limit exceeded")
                raise HTTPException(
                    status_code=429,
                    detail="Amenity search rate limit reached. Please wait and try again.",
                )
            if response.status_code != 200:
                logger.error(f"[Geoapify] HTTP {response.status_code}: {response.text[:300]}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Geoapify returned HTTP {response.status_code}",
                )

            try:
                data = response.json()
            except Exception as json_err:
                logger.error(f"[Geoapify] JSON parse error: {json_err}")
                raise HTTPException(status_code=502, detail="Failed to parse Geoapify response")

            return data.get("features") or []

    except httpx.TimeoutException as e:
        logger.error(f"[Geoapify] Timeout: {type(e).__name__}")
        raise HTTPException(status_code=504, detail="Amenity search timed out. Please try again.")
    except httpx.RequestError as e:
        logger.error(f"[Geoapify] Network error: {type(e).__name__} — {e}")
        raise HTTPException(status_code=502, detail="Failed to reach amenity search service.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Geoapify] Unexpected: {type(e).__name__} — {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


# ── FastAPI route ─────────────────────────────────────────────────────────────

@router.get(
    "/nearby",
    summary="Find nearby amenities via Geoapify Places API (OpenStreetMap data)",
)
async def search_nearby_amenities(
    lat: float,
    lon: float,
    category: str,
    radius_m: int = 1000,
    db: Session = Depends(get_db)
):
    """
    Returns real nearby amenities within radius_m metres of (lat, lon).
    category: washroom | police | medical

    Data: OpenStreetMap via Geoapify Places API (free tier).
    GEOAPIFY_API_KEY is backend-only — never returned to clients.
    """
    if category not in CATEGORY_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {category!r}. Must be one of: {list(CATEGORY_MAP.keys())}",
        )

    cfg = CATEGORY_MAP[category]
    features = await fetch_from_geoapify(lat, lon, cfg["geoapify_categories"], radius_m)

    raw_results = []
    for feature in features:
        normalized = _normalize_feature(feature, category, cfg["default_name"], lat, lon)
        if normalized is not None:
            raw_results.append(normalized)

    # ── Deduplication ────────────────────────────────────────────────────────
    seen_ids = set()
    deduped_results = []
    
    for res in raw_results:
        # 1. Deduplicate by unique Geoapify place_id / osm_id
        if res["id"] and res["id"] in seen_ids:
            continue
            
        # 2. Spatial deduplication
        # - < 5m: Extremely close coordinates, almost certainly a duplicate node
        # - < 20m AND same name: Same facility mapped multiple times (e.g. separate men/women nodes)
        is_duplicate = False
        for existing in deduped_results:
            dist_between = haversine(res["latitude"], res["longitude"], existing["latitude"], existing["longitude"])
            if dist_between < 5:
                is_duplicate = True
                break
            elif dist_between < 20 and res["name"] == existing["name"]:
                is_duplicate = True
                break
                
        if not is_duplicate:
            if res["id"]:
                seen_ids.add(res["id"])
            deduped_results.append(res)

    deduped_results.sort(key=lambda x: x["distance_m"])

    # ── Database Synchronization ─────────────────────────────────────────────
    if category == "washroom":
        for res in deduped_results:
            w_id = res["id"]
            if w_id:
                existing_w = db.query(Washroom).filter(Washroom.id == str(w_id)).first()
                if existing_w:
                    existing_w.name = res["name"]
                    existing_w.address = res["address"]
                    existing_w.latitude = res["latitude"]
                    existing_w.longitude = res["longitude"]
                else:
                    new_w = Washroom(
                        id=str(w_id),
                        name=res["name"],
                        address=res["address"],
                        latitude=res["latitude"],
                        longitude=res["longitude"]
                    )
                    db.add(new_w)
        try:
            db.commit()
            logger.info(f"[Geoapify] Synchronized {len(deduped_results)} washrooms to database.")
        except Exception as e:
            logger.error(f"[Geoapify] Error syncing washrooms to DB: {e}")
            db.rollback()

        # ── Calculate Ratings ───────────────────────────────────────────────
        for res in deduped_results:
            w_id = res["id"]
            if not w_id:
                res["rating"] = None
                res["rating_count"] = 0
                res["is_open"] = None
                res["cleanliness"] = None
                res["safety"] = None
                res["accessible"] = None
                continue
                
            feedbacks = db.query(WashroomFeedback).filter(WashroomFeedback.washroom_id == str(w_id)).all()
            if not feedbacks:
                res["rating"] = None
                res["rating_count"] = 0
                res["is_open"] = None
                res["cleanliness"] = None
                res["safety"] = None
                res["accessible"] = None
                continue
                
            total_rating = 0.0
            valid_feedbacks = 0
            
            is_open_vals = []
            cleanliness_vals = []
            safety_vals = []
            accessible_vals = []
            
            for f in feedbacks:
                row_score = 0
                row_items = 0
                
                if f.is_open is not None:
                    is_open_vals.append(f.is_open)
                if f.cleanliness is not None:
                    cleanliness_vals.append(f.cleanliness)
                if f.safety is not None:
                    safety_vals.append(f.safety)
                if f.accessible is not None:
                    accessible_vals.append(f.accessible)
                
                if f.cleanliness == "Clean":
                    row_score += 5; row_items += 1
                elif f.cleanliness == "Average":
                    row_score += 3; row_items += 1
                elif f.cleanliness == "Dirty":
                    row_score += 1; row_items += 1
                    
                if f.safety == "Safe":
                    row_score += 5; row_items += 1
                elif f.safety == "Concern":
                    row_score += 3; row_items += 1
                elif f.safety == "Unsafe":
                    row_score += 1; row_items += 1
                    
                if f.accessible is True:
                    row_score += 5; row_items += 1
                elif f.accessible is False:
                    row_score += 1; row_items += 1
                    
                if row_items > 0:
                    total_rating += (row_score / row_items)
                    valid_feedbacks += 1
                    
            if valid_feedbacks > 0:
                res["rating"] = round(total_rating / valid_feedbacks, 1)
                res["rating_count"] = valid_feedbacks
            else:
                res["rating"] = None
                res["rating_count"] = 0
                
            res["is_open"] = Counter(is_open_vals).most_common(1)[0][0] if is_open_vals else None
            res["cleanliness"] = Counter(cleanliness_vals).most_common(1)[0][0] if cleanliness_vals else None
            res["safety"] = Counter(safety_vals).most_common(1)[0][0] if safety_vals else None
            res["accessible"] = Counter(accessible_vals).most_common(1)[0][0] if accessible_vals else None

    logger.info(f"[Geoapify] {len(deduped_results)} {category} results for ({lat},{lon}) after deduplication")
    return deduped_results
