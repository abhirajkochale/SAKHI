from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

class CallFriendSettingCreate(BaseModel):
    caller_name: str = Field(..., min_length=1, max_length=50, description="Name of fake caller")
    language_code: str = Field(..., description="Language code: en-IN, hi-IN, mr-IN")
    voice_gender: str = Field(..., description="Voice gender: Male or Female")
    script: str = Field(..., min_length=5, max_length=2500, description="Simulated call script")
    duration_minutes: int = Field(2, description="Duration in minutes: 2, 5, or 10")

    @field_validator("language_code")
    @classmethod
    def validate_language(cls, v: str) -> str:
        valid = ["en-IN", "hi-IN", "mr-IN"]
        if v not in valid:
            raise ValueError(f"language_code must be one of {valid}")
        return v

    @field_validator("voice_gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        valid = ["Male", "Female"]
        if v not in valid:
            raise ValueError(f"voice_gender must be one of {valid}")
        return v

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        valid = [2, 5, 10]
        if v not in valid:
            raise ValueError(f"duration_minutes must be one of {valid}")
        return v

class CallFriendSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    caller_name: str
    language_code: str
    voice_gender: str
    speaker: str
    script: str
    duration_minutes: int
    created_at: datetime
    updated_at: datetime