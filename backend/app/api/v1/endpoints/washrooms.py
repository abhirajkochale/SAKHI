from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import math
from collections import Counter

from app.models.database import get_db
from app.models.washroom import Washroom, WashroomFeedback
from app.schemas.washroom import WashroomResponse, WashroomFeedbackCreate, WashroomListResponse

router = APIRouter()

# Haversine formula for distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3
    phi1 = lat1 * math.pi / 180
    phi2 = lat2 * math.pi / 180
    delta_phi = (lat2 - lat1) * math.pi / 180
    delta_lambda = (lon2 - lon1) * math.pi / 180

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

@router.get("", response_model=WashroomListResponse)
def get_nearby_washrooms(lat: float, lon: float, radius_m: float = 2000.0, db: Session = Depends(get_db)):
    all_washrooms = db.query(Washroom).all()
    nearby = []
    
    for w in all_washrooms:
        dist = haversine(lat, lon, w.latitude, w.longitude)
        if dist <= radius_m:
            feedbacks = w.feedback
            verified_count = len(feedbacks)
            
            is_open_consensus = None
            cleanliness_consensus = None
            safety_consensus = None
            accessible_consensus = None
            last_verified = None
            
            if verified_count > 0:
                is_open_vals = [f.is_open for f in feedbacks if f.is_open is not None]
                if is_open_vals:
                    is_open_consensus = Counter(is_open_vals).most_common(1)[0][0]
                
                cleanliness_vals = [f.cleanliness for f in feedbacks if f.cleanliness is not None]
                if cleanliness_vals:
                    cleanliness_consensus = Counter(cleanliness_vals).most_common(1)[0][0]
                
                safety_vals = [f.safety for f in feedbacks if f.safety is not None]
                if safety_vals:
                    safety_consensus = Counter(safety_vals).most_common(1)[0][0]
                    
                accessible_vals = [f.accessible for f in feedbacks if f.accessible is not None]
                if accessible_vals:
                    accessible_consensus = Counter(accessible_vals).most_common(1)[0][0]
                
                valid_timestamps = [f.timestamp for f in feedbacks if f.timestamp is not None]
                if valid_timestamps:
                    last_verified = max(valid_timestamps)
                    
            nearby.append(WashroomResponse(
                id=w.id,
                name=w.name,
                latitude=w.latitude,
                longitude=w.longitude,
                is_open=is_open_consensus,
                cleanliness=cleanliness_consensus,
                safety=safety_consensus,
                accessible=accessible_consensus,
                verified_count=verified_count,
                last_verified_timestamp=last_verified
            ))
            
    return WashroomListResponse(washrooms=nearby)

@router.post("/{washroom_id}/feedback")
def submit_feedback(washroom_id: str, feedback: WashroomFeedbackCreate, db: Session = Depends(get_db)):
    washroom = db.query(Washroom).filter(Washroom.id == washroom_id).first()
    if not washroom:
        raise HTTPException(status_code=404, detail="Washroom not found")
        
    new_feedback = WashroomFeedback(
        washroom_id=washroom_id,
        is_open=feedback.is_open,
        cleanliness=feedback.cleanliness,
        safety=feedback.safety,
        accessible=feedback.accessible
    )
    
    db.add(new_feedback)
    db.commit()
    return {"status": "success", "message": "Feedback submitted successfully"}
