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
    """Gets or creates the SAKHI User in public.users from verified Supabase token."""
    supabase_user_id = payload.get("sub")
    email = payload.get("email")
    
    if not supabase_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token")
        
    user = db.query(User).filter(User.id == supabase_user_id).first()
    
    if not user:
        # Every new authenticated user ALWAYS defaults strictly to NORMAL status
        user = User(
            id=supabase_user_id,
            email=email,
            display_name=email.split("@")[0] if email else "User",
            identity_provider="google",
            identity_status="NORMAL",
            identity_verified_at=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    return user