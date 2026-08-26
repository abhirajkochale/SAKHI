import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock, AsyncMock
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.call_friend_setting import CallFriendSetting
from datetime import datetime

client = TestClient(app)

MOCK_USER_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

def mock_get_current_user():
    return User(
        id=MOCK_USER_ID,
        email="test@example.com",
        display_name="Test User",
        identity_status="NORMAL"
    )

def test_call_friend_tts_endpoint_mock():
    mock_response = {
        "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",
        "format": "wav",
        "model": "bulbul:v3",
        "language_code": "en-IN",
        "speaker": "shubh"
    }

    with patch("app.api.v1.endpoints.call_friend.generate_sarvam_tts", new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = mock_response

        response = client.post(
            "/api/v1/call-friend/tts",
            json={
                "text": "Hey, where are you? I just wanted to check if you've reached safely.",
                "language_code": "en-IN",
                "speaker": "shubh"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "audio_base64" in data
        assert data["format"] == "wav"
        assert data["model"] == "bulbul:v3"

def test_call_friend_settings_crud_mock():
    mock_setting = CallFriendSetting(
        id="setting-uuid-1",
        user_id=MOCK_USER_ID,
        caller_name="Bro",
        language_code="en-IN",
        voice_gender="Male",
        speaker="shubh",
        script="Hey, where are you? I am checking if you reached safely.",
        duration_minutes=5,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_setting

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    try:
        # 1. GET settings (should return mock_setting)
        response = client.get("/api/v1/call-friend/settings")
        assert response.status_code == 200
        get_data = response.json()
        assert get_data["caller_name"] == "Bro"
        assert get_data["language_code"] == "en-IN"
        assert get_data["voice_gender"] == "Male"

        # 2. POST save settings
        payload = {
            "caller_name": "Mom",
            "language_code": "hi-IN",
            "voice_gender": "Female",
            "script": "??????, ?? ???? ???? ??? ?? ?? ????? ?? ??? ???? ?? ??? ?? ?? ???? ?? ???????? ????? ?? ????",
            "duration_minutes": 2
        }
        response = client.post("/api/v1/call-friend/settings", json=payload)
        assert response.status_code == 200
        post_data = response.json()
        assert post_data["caller_name"] == "Mom"
        assert post_data["language_code"] == "hi-IN"
        assert post_data["voice_gender"] == "Female"
        assert post_data["speaker"] == "ratan"
    finally:
        app.dependency_overrides.clear()