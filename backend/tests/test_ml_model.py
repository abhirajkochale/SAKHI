# pyrefly: ignore [missing-import]
import os
from app.schemas.risk import RiskFeatures
from app.services.risk.ml_model_service import MLModelService

def test_ml_model_unavailable():
    # Provide a fake directory so it fails to load
    service = MLModelService(models_dir="/tmp/fake_dir_does_not_exist")
    assert service.is_available() is False
    assert service.predict(RiskFeatures()) is None

def test_ml_model_available_and_predicts():
    service = MLModelService()
    if not service.is_available():
        return
        
    features = RiskFeatures()
    score = service.predict(features)
    assert score is not None
    assert 0.0 <= score <= 100.0
