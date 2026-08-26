from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from app.services.sarvam_tts import generate_sarvam_tts

router = APIRouter()

class TTSRequest(BaseModel):
    text: str = Field(
        default="Hey, where are you? I just wanted to check if you've reached safely.",
        description="Text content to synthesize into speech"
    )
    language_code: str = Field(
        default="en-IN",
        description="BCP-47 language code (e.g. en-IN, hi-IN)"
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