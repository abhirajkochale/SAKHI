import pytest
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.api.deps import get_current_user
from app.models.user import User

@pytest.fixture
def test_user():
    return User(
        id=str(uuid.uuid4()),
        email="test_users_me@example.com",
        display_name="Me Tester",
        identity_status="NORMAL"
    )

@pytest.fixture
def auth_client(test_user):
    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as c:
        yield c
        
    app.dependency_overrides.clear()

def test_get_me(auth_client, test_user):
    response = auth_client.get("/api/v1/users/me")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["identity_status"] == "NORMAL"
    
    # Should not expose sensitive backend properties like mapped relationships if any exist
    assert "password" not in data
    assert "otp" not in data
