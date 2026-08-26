import httpx
from fastapi import HTTPException, status
from app.core.config import settings
import base64

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

async def generate_sarvam_tts(
    text: str,
    language_code: str = "en-IN",
    speaker: str = "shubh"
) -> dict:
    """
    Calls Sarvam AI Bulbul V3 Text-to-Speech API.
    Returns dictionary with audio_base64 string and format.
    """
    api_key = settings.SARVAM_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SARVAM_API_KEY is not configured on the backend server."
        )

    clean_text = text.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text for TTS cannot be empty."
        )

    if len(clean_text) > 2500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text exceeds maximum limit of 2500 characters for Bulbul V3."
        )

    payload = {
        "inputs": [clean_text],
        "target_language_code": language_code,
        "speaker": speaker,
        "model": "bulbul:v3"
    }

    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(SARVAM_TTS_URL, json=payload, headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Sarvam AI API error ({response.status_code}): {response.text[:200]}"
            )

        data = response.json()
        audios = data.get("audios", [])
        if not audios or not audios[0]:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Sarvam AI API returned empty audio response."
            )

        return {
            "audio_base64": audios[0],
            "format": "wav",
            "model": "bulbul:v3",
            "language_code": language_code,
            "speaker": speaker
        }
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Sarvam AI API: {str(exc)}"
        )