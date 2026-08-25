import httpx
from fastapi import HTTPException
from app.core.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SandboxKycService:
    def __init__(self):
        self.api_key = settings.SANDBOX_API_KEY
        self.api_secret = settings.SANDBOX_API_SECRET
        self.base_url = settings.SANDBOX_BASE_URL.rstrip('/')
        self.access_token: Optional[str] = None

    async def _authenticate(self):
        """Authenticates with the Sandbox API and stores the short-lived access token."""
        if not self.api_key or not self.api_secret:
            logger.error("Sandbox API credentials are missing from environment variables.")
            raise HTTPException(status_code=500, detail="Identity provider is not configured.")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/authenticate",
                    headers={
                        "x-api-key": self.api_key, 
                        "x-api-secret": self.api_secret, 
                        "x-api-version": "1.0.0",
                        "Content-Type": "application/json"
                    },
                    json={},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Sandbox Auth failed with {response.status_code}: {response.text}")
                    raise HTTPException(status_code=500, detail="Identity provider authentication failed.")
                    
                data = response.json()
                self.access_token = data.get("access_token")
                if not self.access_token:
                    logger.error("Sandbox Auth did not return an access_token.")
                    raise HTTPException(status_code=500, detail="Identity provider authentication failed.")
            except httpx.RequestError as e:
                logger.error(f"Sandbox Auth network error: {e}")
                raise HTTPException(status_code=500, detail="Could not reach identity provider.")

    async def _get_headers(self) -> dict:
        if not self.access_token:
            await self._authenticate()
        return {
            "Authorization": str(self.access_token),
            "x-api-key": str(self.api_key),
            "x-api-version": "1.0.0",
            "Content-Type": "application/json"
        }

    async def generate_aadhaar_otp(self, aadhaar_number: str) -> str:
        """
        Requests an OTP to be sent to the mobile number registered with the Aadhaar.
        Returns the reference_id (str) required for the subsequent verification step.
        """
        if not aadhaar_number or len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
            raise HTTPException(status_code=400, detail="Invalid Aadhaar number.")

        headers = await self._get_headers()
        payload = {
            "@entity": "in.co.sandbox.kyc.aadhaar.okyc.otp.request",
            "aadhaar_number": aadhaar_number,
            "consent": "Y",
            "reason": "SAKHI Safety Identity Verification"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/kyc/aadhaar/okyc/otp",
                headers=headers,
                json=payload,
                timeout=15.0
            )
            
            if response.status_code == 401:
                self.access_token = None
                headers = await self._get_headers()
                response = await client.post(
                    f"{self.base_url}/kyc/aadhaar/okyc/otp",
                    headers=headers,
                    json=payload,
                    timeout=15.0
                )
            
            if response.status_code != 200:
                logger.error(f"OTP Generation failed with {response.status_code}: {response.text}")
                try:
                    err_detail = response.json().get("message", "Failed to generate Aadhaar OTP")
                except Exception:
                    err_detail = "Failed to generate Aadhaar OTP"
                raise HTTPException(status_code=400, detail=err_detail)
                
            data = response.json()
            ref_id = data.get("reference_id") or data.get("data", {}).get("reference_id")
            
            if not ref_id:
                logger.error(f"OTP Generation returned 200 but no reference_id: {data}")
                raise HTTPException(status_code=500, detail="Invalid response from identity provider.")
                
            return ref_id

    async def verify_aadhaar_otp(self, reference_id: str, otp: str) -> bool:
        """
        Verifies the provided OTP against the reference_id.
        Returns True if successful, otherwise raises an HTTPException.
        """
        if not reference_id or not otp or not otp.isdigit():
            raise HTTPException(status_code=400, detail="Invalid OTP or reference ID.")

        headers = await self._get_headers()
        payload = {
            "@entity": "in.co.sandbox.kyc.aadhaar.okyc.request",
            "reference_id": reference_id,
            "otp": otp
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/kyc/aadhaar/okyc/otp/verify",
                headers=headers,
                json=payload,
                timeout=15.0
            )
            
            if response.status_code == 401:
                self.access_token = None
                headers = await self._get_headers()
                response = await client.post(
                    f"{self.base_url}/kyc/aadhaar/okyc/otp/verify",
                    headers=headers,
                    json=payload,
                    timeout=15.0
                )
                
            if response.status_code != 200:
                logger.error(f"OTP Verification failed with {response.status_code}: {response.text}")
                try:
                    err_detail = response.json().get("message", "Invalid OTP or verification failed")
                except Exception:
                    err_detail = "Invalid OTP or verification failed"
                raise HTTPException(status_code=400, detail=err_detail)
                
            data = response.json()
            status = data.get("status") or data.get("data", {}).get("status")
            
            if status != "VALID":
                logger.error(f"OTP Verification failed, status was not VALID: {data}")
                raise HTTPException(status_code=400, detail="Verification failed: Aadhaar status is not VALID.")
                
            return True
