from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from math import radians, cos, sin, asin, sqrt

from app.models.database import get_db
from app.models.washroom import Washroom, WashroomFeedback
from app.schemas.washroom import WashroomResponse, WashroomFeedbackCreate
from datetime import datetime

router = APIRouter()

def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance in kilometers between two points on the earth."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers
    return c * r

@router.get("/", response_model=List[WashroomResponse])
def get_washrooms(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = 5.0,
    db: Session = Depends(get_db)
):
    washrooms = db.query(Washroom).all()
    
    if latitude is not None and longitude is not None:
        filtered = []
        for w in washrooms:
            dist = haversine(longitude, latitude, w.longitude, w.latitude)
            if dist <= radius_km:
                filtered.append(w)
        washrooms = filtered

    results = []
    for w in washrooms:
        feedbacks = w.feedbacks
        verified_count = len(feedbacks)
        
        # Default fallback values
        is_open = True
        cleanliness = "Clean"
        safety = "Safe"
        accessible = False
        last_verified_timestamp = None

        if verified_count > 0:
            last_verified_timestamp = max(f.timestamp for f in feedbacks)
            
            # Majority logic
            open_count = sum(1 for f in feedbacks if f.is_open)
            is_open = open_count >= (verified_count / 2)

            accessible_count = sum(1 for f in feedbacks if f.accessible)
            accessible = accessible_count >= (verified_count / 2)

            from collections import Counter
            cleanliness_counts = Counter(f.cleanliness for f in feedbacks)
            cleanliness = cleanliness_counts.most_common(1)[0][0]

            safety_counts = Counter(f.safety for f in feedbacks)
            safety = safety_counts.most_common(1)[0][0]

        results.append(WashroomResponse(
            id=w.id,
            name=w.name,
            address=w.address,
            latitude=w.latitude,
            longitude=w.longitude,
            is_open=is_open,
            cleanliness=cleanliness,
            safety=safety,
            accessible=accessible,
            verified_count=verified_count,
            last_verified_timestamp=last_verified_timestamp
        ))
    
    return results

@router.post("/{washroom_id}/feedback", response_model=dict)
def submit_feedback(
    washroom_id: int,
    feedback: WashroomFeedbackCreate,
    db: Session = Depends(get_db)
):
    washroom = db.query(Washroom).filter(Washroom.id == washroom_id).first()
    if not washroom:
        raise HTTPException(status_code=404, detail="Washroom not found")

    new_feedback = WashroomFeedback(
        washroom_id=washroom_id,
        is_open=feedback.is_open,
        cleanliness=feedback.cleanliness,
        safety=feedback.safety,
        accessible=feedback.accessible,
        timestamp=datetime.utcnow()
    )
    
    db.add(new_feedback)
    db.commit()
    
    return {"status": "success", "message": "Feedback submitted successfully."}
