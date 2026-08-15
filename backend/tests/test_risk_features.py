import math
from datetime import datetime
from app.schemas.journey import JourneySegment, Location
from app.schemas.risk import SegmentContext
from app.services.risk.feature_service import FeatureExtractionService

def test_extract_features_temporal():
    service = FeatureExtractionService()
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    # Test Midnight (Friday)
    dt = datetime(2026, 8, 14, 0, 0)
    context = SegmentContext(departure_time=dt)
    features = service.extract_features(segment, context)
    
    assert features.is_weekend == 0.0
    assert math.isclose(features.hour_cos, 1.0, abs_tol=1e-5)
    assert math.isclose(features.hour_sin, 0.0, abs_tol=1e-5)
    
    # Test Noon (Saturday)
    dt = datetime(2026, 8, 15, 12, 0)
    context = SegmentContext(departure_time=dt)
    features = service.extract_features(segment, context)
    
    assert features.is_weekend == 1.0
    assert math.isclose(features.hour_cos, -1.0, abs_tol=1e-5)
    assert math.isclose(features.hour_sin, 0.0, abs_tol=1e-5)

def test_extract_features_isolation():
    service = FeatureExtractionService()
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    context = SegmentContext(footfall_indicator=0.8)
    features = service.extract_features(segment, context)
    
    # High footfall (0.8) should mean low isolation (0.2)
    assert math.isclose(features.environmental_isolation_indicator, 0.2, abs_tol=1e-5)

def test_extract_features_missing_context():
    service = FeatureExtractionService()
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    context = SegmentContext()
    features = service.extract_features(segment, context)
    
    assert features.hour_sin == 0.0
    assert features.environmental_isolation_indicator == 1.0
    assert features.cctv_coverage == 0.0
    assert features.historical_baseline == 0.5  # Neutral default
