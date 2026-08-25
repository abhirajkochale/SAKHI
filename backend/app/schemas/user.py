from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    identity_status: str
    identity_provider: Optional[str] = None
    identity_verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
