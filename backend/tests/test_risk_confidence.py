from datetime import datetime
from app.schemas.risk import SegmentContext
from app.services.risk.confidence_service import ConfidenceService

def test_confidence_full_context():
    service = ConfidenceService()
    context = SegmentContext(
        departure_time=datetime.now(),
        historical_baseline=0.5,
        footfall_indicator=0.8,
        cctv_coverage=1.0,
        police_proximity=0.5,
        infrastructure_score=0.8,
        transit_access=1.0
    )
    score, level = service.calculate_confidence(context)
    assert score == 100.0
    assert level == "HIGH"

def test_confidence_missing_context():
    service = ConfidenceService()
    # Missing footfall (-20), departure_time (-20), and transit_access (-10)
    context = SegmentContext(
        historical_baseline=0.5,
        cctv_coverage=1.0,
        police_proximity=0.5,
        infrastructure_score=0.8
    )
    score, level = service.calculate_confidence(context)
    assert score == 50.0
    assert level == "MEDIUM"

def test_confidence_insufficient_data():
    service = ConfidenceService()
    # completely empty context
    context = SegmentContext()
    score, level = service.calculate_confidence(context)
    assert score == 0.0
    assert level == "Insufficient Data"
