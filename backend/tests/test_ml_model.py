import os
from app.schemas.risk import RiskFeatures
from app.services.risk.ml_model_service import MLModelService

def test_ml_model_unavailable():
    # Provide a fake directory so it fails to load
    service = MLModelService(models_dir="/tmp/fake_dir_does_not_exist")
    assert service.is_available() is False
    assert service.predict(RiskFeatures(
        hour_sin=0.0, hour_cos=0.0, is_weekend=0.0,
        environmental_isolation_indicator=0.0, cctv_coverage=0.0,
        police_proximity=0.0, transit_access=0.0,
        infrastructure_score=0.0, historical_baseline=0.0,
        validated_report_signal=0.0
    )) is None

def test_ml_model_available_and_predicts():
    service = MLModelService()
    # Assuming the model is generated during testing or before
    if not service.is_available():
        # skip if not run after train.py
        return
        
    features = RiskFeatures(
        hour_sin=0.0, hour_cos=1.0, is_weekend=1.0,
        environmental_isolation_indicator=0.8, cctv_coverage=0.2,
        police_proximity=0.1, transit_access=0.5,
        infrastructure_score=0.4, historical_baseline=0.7,
        validated_report_signal=0.0
    )
    score = service.predict(features)
    assert score is not None
    assert 0.0 <= score <= 100.0
