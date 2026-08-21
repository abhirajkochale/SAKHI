# pyrefly: ignore [missing-import]
from datetime import datetime
from app.schemas.risk import SegmentContext
from app.services.risk.confidence_service import ConfidenceService

def test_confidence_full_context():
    service = ConfidenceService()
    context = SegmentContext(
        departure_time=datetime.now(),
        lighting_data_synthetic=False,
        cctv_data_synthetic=False,
        mobility_data_synthetic=False,
        hotspot_data_synthetic=False,
        nearest_segment_distance_m=100,
        infrastructure_distances_real=True,
        district_baseline_real=True
    )
    score, level = service.calculate_confidence(context)
    assert score == 100.0
    assert level == "HIGH"

def test_confidence_missing_context():
    service = ConfidenceService()
    context = SegmentContext(
        departure_time=None,
        lighting_data_synthetic=True,
        cctv_data_synthetic=True,
        mobility_data_synthetic=True,
        hotspot_data_synthetic=True,
        nearest_segment_distance_m=None,
        infrastructure_distances_real=True,
        district_baseline_real=True
    )
    score, level = service.calculate_confidence(context)
    assert score == 58.2
    assert level == "MEDIUM"

def test_confidence_insufficient_data():
    service = ConfidenceService()
    context = SegmentContext(
        departure_time=None,
        lighting_data_synthetic=True,
        cctv_data_synthetic=True,
        mobility_data_synthetic=True,
        hotspot_data_synthetic=True,
        nearest_segment_distance_m=10000,
        infrastructure_distances_real=False,
        district_baseline_real=False
    )
    score, level = service.calculate_confidence(context)
    assert score == 35.45
    assert level == "LOW"
