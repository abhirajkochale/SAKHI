from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import os
from datetime import datetime
from typing import Optional
from app.models.database import get_db
from app.models.user import User
from app.core.config import settings

SUPABASE_URL = settings.SUPABASE_URL
if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL environment variable is missing")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
ISSUER = f"{SUPABASE_URL}/auth/v1"

jwks_client = jwt.PyJWKClient(JWKS_URL)
security = HTTPBearer()

def verify_supabase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        unverified_header = jwt.get_unverified_header(token)
        algorithm = unverified_header.get("alg")
        
        if not algorithm:
            raise HTTPException(status_code=401, detail="No alg found in token header")

        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            issuer=ISSUER,
            options={"verify_aud": False}
        )
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid authentication credentials: {str(e)}")

def get_current_user(
    payload: dict = Depends(verify_supabase_token),
    db: Session = Depends(get_db)
) -> User:
    supabase_user_id = payload.get("sub")
    email = payload.get("email")
    
    # Safe robust parsing of user_metadata
    user_metadata = payload.get("user_metadata", {})
    if not isinstance(user_metadata, dict):
        user_metadata = {}
        
    raw_demo = user_metadata.get("demo_identity_verified", False)
    
    # Force strict boolean evaluation
    demo_verified = False
    if isinstance(raw_demo, bool):
        demo_verified = raw_demo
    elif isinstance(raw_demo, str):
        demo_verified = raw_demo.lower() == "true"
        
    if not supabase_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token")
        
    user = db.query(User).filter(User.id == supabase_user_id).first()
    
    if not user:
        user = User(
            id=supabase_user_id,
            email=email,
            display_name=email.split("@")[0] if email else "User",
            identity_status="VERIFIED" if demo_verified else "NORMAL",
            identity_verified_at=datetime.utcnow() if demo_verified else None
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        needs_update = False
        if demo_verified and user.identity_status != "VERIFIED":
            user.identity_status = "VERIFIED"
            user.identity_verified_at = datetime.utcnow()
            needs_update = True
            
        if needs_update:
            db.commit()
            db.refresh(user)
        
    return user