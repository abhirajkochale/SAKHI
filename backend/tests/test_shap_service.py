# pyrefly: ignore [missing-import]
import math
from datetime import datetime
from app.schemas.journey import JourneySegment, Location
from app.schemas.risk import RiskFeatures, SegmentContext
from app.services.risk.ml_model_service import MLModelService
from app.services.risk.shap_service import SHAPService
from app.services.risk.risk_service import RiskService

def test_shap_service_loads_and_explains():
    ml_service = MLModelService()
    if not ml_service.is_available():
        return
        
    shap_service = SHAPService(ml_service)
    
    features = RiskFeatures()
    predicted_risk = ml_service.predict(features)
    
    explanation = shap_service.explain(features, predicted_risk)
    
    assert explanation.available is True
    assert math.isclose(explanation.predicted_risk, predicted_risk, abs_tol=1e-2)
    assert explanation.all_contributions is not None
    assert len(explanation.all_contributions) == 27
    
    # Check directions
    for contrib in explanation.all_contributions:
        if contrib.shap_value > 0:
            assert contrib.direction == "increases_risk"
        else:
            assert contrib.direction == "decreases_risk"
            
    # Check sorting (by absolute magnitude)
    if len(explanation.all_contributions) > 1:
        assert abs(explanation.all_contributions[0].shap_value) >= abs(explanation.all_contributions[1].shap_value)

    # Check additivity
    sum_shap = sum(c.shap_value for c in explanation.all_contributions)
    assert math.isclose(explanation.base_value + sum_shap, predicted_risk, abs_tol=1.0)

def test_shap_fallback_missing_model():
    ml_service = MLModelService(models_dir="/tmp/fake")
    shap_service = SHAPService(ml_service)
    
    features = RiskFeatures()
    
    explanation = shap_service.explain(features, 50.0)
    assert explanation.available is False
    assert "not available" in explanation.reason or "not active" in explanation.reason

def test_risk_service_fallback_does_not_fabricate_shap():
    service = RiskService()
    service.ml_service = MLModelService(models_dir="/tmp/fake")
    service.shap_service = SHAPService(service.ml_service)
    
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    context = SegmentContext()
    
    risk_score = service.calculate_risk(segment, context)
    
    assert risk_score.model_source == "heuristic"
    assert risk_score.explanation is not None
    assert risk_score.explanation.available is False

def test_confidence_remains_independent():
    service = RiskService()
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    context = SegmentContext()
    risk_score = service.calculate_risk(segment, context)
    
    assert risk_score.confidence_score > 0.0
