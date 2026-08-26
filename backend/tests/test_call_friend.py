import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

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