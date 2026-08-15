import math
from datetime import datetime
from app.schemas.journey import JourneySegment, Location
from app.schemas.risk import SegmentContext
from app.services.risk.risk_service import RiskService

def test_calculate_risk_deterministic():
    service = RiskService()
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    # Let's create a specific context to test the heuristic math
    # Base risk (historical): 0.5 * 40 = 20
    # Isolation: footfall=0.8 -> isolation=0.2 * 30 = 6
    # Lack of infra: infra=1.0 -> 0 * 15 = 0
    # Lack of cctv: cctv=1.0 -> 0 * 10 = 0
    # Lack of police: police=1.0 -> 0 * 5 = 0
    # Time penalty: noon -> cos=-1 -> max(0, -1) = 0 * 10 = 0
    # Report risk: 0 * 20 = 0
    # Total = 20 + 6 = 26
    
    dt = datetime(2026, 8, 15, 12, 0) # Noon
    context = SegmentContext(
        departure_time=dt,
        historical_baseline=0.5,
        footfall_indicator=0.8,
        infrastructure_score=1.0,
        cctv_coverage=1.0,
        police_proximity=1.0,
        transit_access=1.0,
        validated_report_signal=0.0
    )
    
    risk_score = service.calculate_risk(segment, context)
    
    assert risk_score.segment_id == "123"
    assert math.isclose(risk_score.risk_score, 26.0, abs_tol=1e-5)
    assert risk_score.confidence_score == 100.0
    assert risk_score.confidence_level == "HIGH"
    
def test_calculate_risk_bounds():
    service = RiskService()
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    # Worst case scenario
    dt = datetime(2026, 8, 15, 0, 0) # Midnight
    context = SegmentContext(
        departure_time=dt,
        historical_baseline=1.0,
        footfall_indicator=0.0,
        infrastructure_score=0.0,
        cctv_coverage=0.0,
        police_proximity=0.0,
        validated_report_signal=1.0
    )
    
    risk_score = service.calculate_risk(segment, context)
    # The heuristic might add up to > 100, we must bound it.
    # 40 + 30 + 15 + 10 + 5 + 10 + 20 = 130
    assert risk_score.risk_score == 100.0

def test_calculate_risk_missing_context():
    service = RiskService()
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    # Completely empty context
    context = SegmentContext()
    
    risk_score = service.calculate_risk(segment, context)
    assert risk_score.confidence_score == 0.0
    assert risk_score.confidence_level == "Insufficient Data"
    # Even with insufficient data, we still generate a baseline risk using defaults
    assert 0.0 <= risk_score.risk_score <= 100.0
