from sqlalchemy.orm import Session
from app.models.incident import Incident
from app.models.route_segment import PersistentRouteSegment
from datetime import datetime

def recalculate_segment_risk(db: Session, segment_id: str):
    # Find the segment
    segment = db.query(PersistentRouteSegment).filter(PersistentRouteSegment.segment_id == segment_id).first()
    
    if not segment:
        # Create it if it doesn't exist
        segment = PersistentRouteSegment(
            segment_id=segment_id,
            base_risk_score=0.0,
            base_confidence_score=1.0
        )
        db.add(segment)
        db.commit()
        db.refresh(segment)

    # Get all active incidents for this segment
    incidents = db.query(Incident).filter(Incident.segment_id == segment_id, Incident.active == 1).all()
    
    # Calculate new risk
    # This is a basic algorithm for the prototype: 
    # increase base risk score by a fraction of the incident severity
    
    total_severity = sum([incident.severity for incident in incidents])
    
    # We use a simple decay or capped model for prototype.
    # Max risk is 100.
    new_risk_score = min(100.0, segment.base_risk_score + (total_severity * 0.5))
    
    segment.base_risk_score = new_risk_score
    segment.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(segment)
    return segment
