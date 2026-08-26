from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
from app.services.sarvam_tts import generate_sarvam_tts
from app.api.deps import get_current_user
from app.models.user import User
from app.models.call_friend_setting import CallFriendSetting
from app.models.database import get_db
from app.schemas.call_friend import CallFriendSettingCreate, CallFriendSettingResponse

router = APIRouter()

def get_speaker_for_gender_and_language(language_code: str, voice_gender: str) -> str:
    if voice_gender.lower() == "female":
        return "ratan"
    return "shubh"

class TTSRequest(BaseModel):
    text: str = Field(
        default="Hey, where are you? I just wanted to check if you've reached safely.",
        description="Text content to synthesize into speech"
    )
    language_code: str = Field(
        default="en-IN",
        description="BCP-47 language code (e.g. en-IN, hi-IN, mr-IN)"
    )
    speaker: str = Field(
        default="shubh",
        description="Sarvam Bulbul V3 speaker name"
    )

class TTSResponse(BaseModel):
    audio_base64: str
    format: str = "wav"
    model: str = "bulbul:v3"
    language_code: str
    speaker: str

@router.post("/tts", response_model=TTSResponse, summary="Generate Sarvam AI Bulbul V3 TTS Audio for Call a Friend")
async def create_tts_audio(request: TTSRequest):
    """
    Proof-of-concept endpoint to convert text to speech using Sarvam AI Bulbul V3.
    """
    result = await generate_sarvam_tts(
        text=request.text,
        language_code=request.language_code,
        speaker=request.speaker
    )
    return result

@router.get("/settings", response_model=CallFriendSettingResponse, summary="Get current user's Call a Friend settings")
def get_user_call_friend_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    setting = db.query(CallFriendSetting).filter(CallFriendSetting.user_id == current_user.id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Call a Friend settings found for current user."
        )
    return setting

@router.post("/settings", response_model=CallFriendSettingResponse, summary="Save or update current user's Call a Friend settings")
def save_user_call_friend_settings(
    payload: CallFriendSettingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    speaker = get_speaker_for_gender_and_language(payload.language_code, payload.voice_gender)
    
    setting = db.query(CallFriendSetting).filter(CallFriendSetting.user_id == current_user.id).first()
    if not setting:
        setting = CallFriendSetting(
            user_id=current_user.id,
            caller_name=payload.caller_name,
            language_code=payload.language_code,
            voice_gender=payload.voice_gender,
            speaker=speaker,
            script=payload.script,
            duration_minutes=payload.duration_minutes
        )
        db.add(setting)
    else:
        setting.caller_name = payload.caller_name
        setting.language_code = payload.language_code
        setting.voice_gender = payload.voice_gender
        setting.speaker = speaker
        setting.script = payload.script
        setting.duration_minutes = payload.duration_minutes

    db.commit()
    db.refresh(setting)
    return setting