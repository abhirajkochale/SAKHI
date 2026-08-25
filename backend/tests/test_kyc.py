import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import Response
import uuid

from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from app.models.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
@pytest.fixture
def test_user():
    return User(
        id=str(uuid.uuid4()),
        email=f"test_kyc_{uuid.uuid4().hex[:6]}@example.com",
        display_name="KYC Tester",
        identity_status="NORMAL"
    )

@pytest.fixture
def test_other_user():
    return User(
        id=str(uuid.uuid4()),
        email=f"other_kyc_{uuid.uuid4().hex[:6]}@example.com",
        display_name="Other Tester",
        identity_status="NORMAL"
    )

@pytest.fixture
def auth_client(test_user, db_session):
    def override_get_current_user():
        return test_user
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    
    # ensure user exists in db
    db_session.add(test_user)
    db_session.commit()
    
    with TestClient(app) as c:
        yield c
        
    app.dependency_overrides.clear()

def test_aadhaar_otp_generation_success(auth_client):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [
            Response(200, json={"access_token": "mock_token"}),
            Response(200, json={"reference_id": "mock_ref_123"}),
        ]
        
        response = auth_client.post(
            "/api/v1/kyc/aadhaar/init",
            json={"aadhaar_number": "123412341234"}
        )
        
        assert response.status_code == 200
        assert response.json()["reference_id"] == "mock_ref_123"
        assert "aadhaar_number" not in response.json()
        
        # Assert auth endpoint & headers
        auth_call = mock_post.call_args_list[0]
        assert auth_call[0][0] == "https://test-api.sandbox.co.in/authenticate"
        assert "x-api-key" in auth_call[1]["headers"]
        assert "x-api-secret" in auth_call[1]["headers"]
        assert auth_call[1]["headers"]["x-api-version"] == "1.0.0"
        
        # Assert generate OTP endpoint & headers
        generate_call = mock_post.call_args_list[1]
        assert generate_call[0][0] == "https://test-api.sandbox.co.in/kyc/aadhaar/okyc/otp"
        assert generate_call[1]["headers"]["Authorization"] == "mock_token"

def test_aadhaar_otp_generation_invalid_aadhaar(auth_client):
    response = auth_client.post(
        "/api/v1/kyc/aadhaar/init",
        json={"aadhaar_number": "123"}
    )
    assert response.status_code == 422

def test_aadhaar_otp_generation_auth_failure(auth_client):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = Response(401, json={"error": "unauthorized"})
        
        response = auth_client.post(
            "/api/v1/kyc/aadhaar/init",
            json={"aadhaar_number": "123412341234"}
        )
        
        assert response.status_code == 500
        assert "Identity provider authentication failed" in response.json()["detail"]

def test_aadhaar_otp_generation_api_failure(auth_client):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [
            Response(200, json={"access_token": "mock_token"}),
            Response(422, json={"message": "Invalid Aadhaar"}),
        ]
        
        response = auth_client.post(
            "/api/v1/kyc/aadhaar/init",
            json={"aadhaar_number": "123412341234"}
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid Aadhaar"

def test_aadhaar_otp_verification_success(auth_client, test_user, db_session):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [
            Response(200, json={"access_token": "mock_token"}),
            Response(200, json={"status": "VALID", "message": "Verified"}),
        ]
        
        response = auth_client.post(
            "/api/v1/kyc/aadhaar/verify",
            json={"reference_id": "mock_ref_123", "otp": "123456"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        verify_call = mock_post.call_args_list[1]
        assert verify_call[0][0] == "https://test-api.sandbox.co.in/kyc/aadhaar/okyc/otp/verify"
        
        db_session.refresh(test_user)
        assert test_user.identity_status == "VERIFIED"
        assert test_user.identity_provider == "sandbox_aadhaar"
        assert test_user.identity_verified_at is not None
        
        assert not hasattr(test_user, "otp")
        assert not hasattr(test_user, "aadhaar_number")

def test_aadhaar_otp_verification_failure_status(auth_client, test_user, db_session):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [
            Response(200, json={"access_token": "mock_token"}),
            Response(200, json={"status": "INVALID"}),
        ]
        
        response = auth_client.post(
            "/api/v1/kyc/aadhaar/verify",
            json={"reference_id": "mock_ref_123", "otp": "000000"}
        )
        
        assert response.status_code == 400
        assert "Aadhaar status is not VALID" in response.json()["detail"]
        
        db_session.refresh(test_user)
        assert test_user.identity_status == "NORMAL"

def test_aadhaar_otp_verification_failure(auth_client, test_user, db_session):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [
            Response(200, json={"access_token": "mock_token"}),
            Response(422, json={"message": "Invalid OTP"}),
        ]
        
        response = auth_client.post(
            "/api/v1/kyc/aadhaar/verify",
            json={"reference_id": "mock_ref_123", "otp": "000000"}
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid OTP"
        
        db_session.refresh(test_user)
        assert test_user.identity_status == "NORMAL"

def test_kyc_isolation(auth_client, test_user, test_other_user, db_session):
    db_session.add(test_other_user)
    db_session.commit()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [
            Response(200, json={"access_token": "mock_token"}),
            Response(200, json={"status": "VALID"}),
        ]
        
        auth_client.post(
            "/api/v1/kyc/aadhaar/verify",
            json={"reference_id": "mock_ref_123", "otp": "123456"}
        )
        
        db_session.refresh(test_user)
        db_session.refresh(test_other_user)
        
        assert test_user.identity_status == "VERIFIED"
        assert test_other_user.identity_status == "NORMAL"
