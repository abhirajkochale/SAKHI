# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "sakhi-backend"
    assert body["database"] == "connected"
