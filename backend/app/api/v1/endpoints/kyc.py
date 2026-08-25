from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.schemas.kyc import (
    AadhaarOtpRequest, AadhaarOtpResponse, 
    AadhaarVerifyRequest, AadhaarVerifyResponse,
    AadhaarDemoRequest, AadhaarDemoResponse
)
from app.services.kyc.sandbox_kyc_service import SandboxKycService

router = APIRouter()

# Dependency injection for the service
def get_kyc_service() -> SandboxKycService:
    return SandboxKycService()

@router.post("/aadhaar/init", response_model=AadhaarOtpResponse, summary="Generate Aadhaar OTP")
async def init_aadhaar_verification(
    request: AadhaarOtpRequest,
    current_user: User = Depends(get_current_user),
    kyc_service: SandboxKycService = Depends(get_kyc_service)
):
    """
    Initiates Aadhaar KYC by requesting an OTP.
    Requires an authenticated user token.
    The Aadhaar number is NOT stored in the database.
    """
    ref_id = await kyc_service.generate_aadhaar_otp(request.aadhaar_number)
    return AadhaarOtpResponse(reference_id=ref_id)

@router.post("/aadhaar/verify", response_model=AadhaarVerifyResponse, summary="Verify Aadhaar OTP")
async def verify_aadhaar_otp(
    request: AadhaarVerifyRequest,
    current_user: User = Depends(get_current_user),
    kyc_service: SandboxKycService = Depends(get_kyc_service),
    db: Session = Depends(get_db)
):
    """
    Verifies the Aadhaar OTP.
    If successful, upgrades the authenticated user's identity_status to VERIFIED.
    The OTP and reference ID are not persisted.
    """
    # 1. Call the sandbox provider to verify the OTP
    success = await kyc_service.verify_aadhaar_otp(request.reference_id, request.otp)
    
    # 2. If successful, update the user in our database
    if success:
        current_user.identity_status = "VERIFIED"
        current_user.identity_provider = "sandbox_aadhaar"
        current_user.identity_verified_at = datetime.utcnow()
        
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
        
    return AadhaarVerifyResponse(
        status="success",
        message="User identity verified successfully"
    )

@router.post("/aadhaar/demo", response_model=AadhaarDemoResponse, summary="Hackathon Demo Aadhaar Verification")
async def verify_aadhaar_demo(
    request: AadhaarDemoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulates Aadhaar verification for hackathon demo purposes.
    Only accepts designated test numbers (e.g., 999999990019).
    """
    digits_only = request.aadhaar_number.strip()
    if digits_only != "999999990019":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid demo Aadhaar number. Use the designated test value (999999990019).")
        
    if current_user.identity_status == "VERIFIED":
        # Do not overwrite a real VERIFIED status with DEMO
        return AadhaarDemoResponse(status="demo_verified", display_name="Demo User")
        
    current_user.identity_status = "VERIFIED_DEMO"
    current_user.identity_provider = "aadhaar_demo"
    current_user.identity_verified_at = datetime.utcnow()
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return AadhaarDemoResponse(status="demo_verified", display_name="Demo User")
