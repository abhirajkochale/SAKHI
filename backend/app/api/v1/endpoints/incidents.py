from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.incident import Incident
from app.schemas.context import IncidentCreate, IncidentResponse
from app.services.context_update_service import ContextUpdateService

router = APIRouter()

def process_incident_background(incident_id: int):
    # This background task handles recalculating the route segment's persistent risk
    service = ContextUpdateService()
    service.process_incident_from_db(incident_id)

@router.post("/", response_model=IncidentResponse, status_code=201)
def report_incident(
    incident_in: IncidentCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # 1. Save to Database
    db_incident = Incident(
        segment_id=incident_in.segment_id,
        event_type=incident_in.event_type,
        severity=incident_in.severity,
        latitude=incident_in.latitude,
        longitude=incident_in.longitude,
        description=incident_in.description
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    
    # 2. Trigger asynchronous risk recalculation
    background_tasks.add_task(process_incident_background, db_incident.id)
    
    return db_incident
