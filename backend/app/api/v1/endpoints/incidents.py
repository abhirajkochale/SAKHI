from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.schemas.incident import IncidentCreate, IncidentResponse
from app.models.incident import Incident
from app.services.risk.calibration_service import recalculate_segment_risk
from typing import List

router = APIRouter()

from app.api.deps import get_current_user
from app.models.user import User

@router.post("/", response_model=IncidentResponse, status_code=201)
def report_incident(
    incident_in: IncidentCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Save the incident
    new_incident = Incident(
        user_id=current_user.id,
        segment_id=incident_in.segment_id,
        event_type=incident_in.event_type,
        severity=incident_in.severity,
        latitude=incident_in.latitude,
        longitude=incident_in.longitude,
        description=incident_in.description
    )
    
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    
    # Trigger background task to dynamically recalculate segment risk score
    background_tasks.add_task(recalculate_segment_risk, db, new_incident.segment_id)
    
    return new_incident

@router.get("/", response_model=List[IncidentResponse])
def get_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).all()
