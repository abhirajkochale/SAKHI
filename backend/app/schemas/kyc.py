from pydantic import BaseModel, Field

class AadhaarOtpRequest(BaseModel):
    aadhaar_number: str = Field(..., min_length=12, max_length=12, description="12-digit Aadhaar Number")

class AadhaarOtpResponse(BaseModel):
    reference_id: str = Field(..., description="Provider reference ID for OTP verification")

class AadhaarVerifyRequest(BaseModel):
    reference_id: str = Field(..., description="Provider reference ID from the OTP generation step")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")

class AadhaarVerifyResponse(BaseModel):
    status: str = Field(..., description="Verification status")
    message: str = Field(..., description="Human readable message")

class AadhaarDemoRequest(BaseModel):
    aadhaar_number: str = Field(..., min_length=12, max_length=12, description="12-digit Demo Aadhaar Number")

class AadhaarDemoResponse(BaseModel):
    status: str
    display_name: str
