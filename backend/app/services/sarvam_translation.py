import httpx
from fastapi import HTTPException, status
from app.core.config import settings

SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"

async def translate_text(
    text: str,
    source_language_code: str,
    target_language_code: str,
    speaker_gender: str = "Female"
) -> str:
    """
    Translates text between supported Indian languages / English using Sarvam AI Translation API.
    If source and target language codes are identical, returns original text without API call.
    """
    clean_text = text.strip()
    if not clean_text:
        return ""

    if source_language_code == target_language_code:
        return clean_text

    api_key = settings.SARVAM_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SARVAM_API_KEY is not configured on the backend server."
        )

    formatted_gender = "Female" if speaker_gender.lower() == "female" else "Male"

    payload = {
        "input": clean_text,
        "source_language_code": source_language_code,
        "target_language_code": target_language_code,
        "speaker_gender": formatted_gender,
        "mode": "formal"
    }

    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json; charset=utf-8"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(SARVAM_TRANSLATE_URL, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Sarvam AI Translation API error ({response.status_code}): {response.text[:200]}"
            )

        data = response.json()
        translated_text = data.get("translated_text")
        if not translated_text:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Sarvam AI Translation API returned empty response."
            )

        return translated_text
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Sarvam AI Translation API: {str(exc)}"
        )
