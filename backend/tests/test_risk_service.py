# pyrefly: ignore [missing-import]
import math
from datetime import datetime
from app.schemas.journey import JourneySegment, Location
from app.schemas.risk import SegmentContext
from app.services.risk.risk_service import RiskService

def test_calculate_risk_deterministic():
    service = RiskService()
    # Force fallback to test heuristic math
    from app.services.risk.ml_model_service import MLModelService
    service.ml_service = MLModelService(models_dir="/tmp/fake")
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    dt = datetime(2026, 8, 15, 12, 0) # Noon
    context = SegmentContext(departure_time=dt)
    
    risk_score = service.calculate_risk(segment, context)
    
    assert risk_score.segment_id == "123"
    assert 0.0 <= risk_score.risk_score <= 100.0
    assert risk_score.confidence_score > 0.0
    assert risk_score.model_source == "heuristic"
    assert risk_score.model_version is not None
    
def test_calculate_risk_bounds():
    service = RiskService()
    # Force fallback to test heuristic math
    from app.services.risk.ml_model_service import MLModelService
    service.ml_service = MLModelService(models_dir="/tmp/fake")
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    # Worst case scenario
    dt = datetime(2026, 8, 15, 0, 0) # Midnight
    context = SegmentContext(
        departure_time=dt,
        validated_report_signal=1.0
    )
    
    risk_score = service.calculate_risk(segment, context)
    assert 0.0 <= risk_score.risk_score <= 100.0

def test_calculate_risk_missing_context():
    service = RiskService()
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    context = SegmentContext()
    risk_score = service.calculate_risk(segment, context)
    assert risk_score.confidence_score > 0.0
    assert 0.0 <= risk_score.risk_score <= 100.0
