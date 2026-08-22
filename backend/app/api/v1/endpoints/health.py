from fastapi import APIRouter

router = APIRouter()

from app.db.connection import get_db

@router.get("/health", summary="Health check")
async def health_check():
    db_status = "error"
    try:
        db = await get_db()
        await db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "status": "ok",
        "service": "sakhi-backend",
        "database": db_status
    }
