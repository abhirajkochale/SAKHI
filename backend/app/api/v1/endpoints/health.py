from fastapi import APIRouter

router = APIRouter()

from app.models.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Depends

@router.get("/health", summary="Health check")
def health_check(db: Session = Depends(get_db)):
    db_status = "error"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "status": "ok",
        "service": "sakhi-backend",
        "database": db_status
    }
