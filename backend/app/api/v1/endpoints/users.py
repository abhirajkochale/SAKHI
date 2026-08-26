from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.models.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter()

@router.get("/me", response_model=UserResponse, summary="Get current authenticated user profile")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve the profile metadata for the currently authenticated user.
    Uses the verified JWT token to guarantee identity.
    """
    return current_user

@router.post("/me/verify-demo", response_model=UserResponse, summary="Verify current user with 12-digit demo code")
def verify_demo_user(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the authenticated user's identity_status to VERIFIED in public.users
    when a valid 12-digit demo code is submitted.
    """
    demo_code = str(payload.get("demo_code", "")).strip()
    if not demo_code or not demo_code.isdigit() or len(demo_code) != 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid demo code. Must be exactly 12 numeric digits."
        )
        
    current_user.identity_status = "VERIFIED"
    current_user.identity_verified_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return current_user