# pyrefly: ignore [missing-import]
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
    features = service.extract(segment, context)
    
    assert features.is_weekend == 0.0
    assert math.isclose(features.representative_hour, 0.0, abs_tol=1e-5)
    assert features.is_night == 1.0
    assert features.is_late_night == 1.0
    
    # Test Noon (Saturday)
    dt = datetime(2026, 8, 15, 12, 0)
    context = SegmentContext(departure_time=dt)
    features = service.extract(segment, context)
    
    assert features.is_weekend == 1.0
    assert math.isclose(features.representative_hour, 12.0, abs_tol=1e-5)
    assert features.is_night == 0.0

def test_extract_features_isolation():
    service = FeatureExtractionService()
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    context = SegmentContext(footfall_indicator=0.8)
    features = service.extract(segment, context)
    
    # Assert footfall proxy is a valid positive float scaled by indicator
    assert features.footfall_proxy > 0.0

def test_extract_features_missing_context():
    service = FeatureExtractionService()
    segment = JourneySegment(
        segment_id="123", journey_id="456", sequence=1, mode="walking",
        start_location=Location(latitude=0, longitude=0), end_location=Location(latitude=0, longitude=0),
        distance_m=10, duration_s=10, geometry={"type": "LineString", "coordinates": []}
    )
    
    context = SegmentContext()
    features = service.extract(segment, context)
    
    # Feature scores should be in valid normalized/raw bounds
    assert 0.0 <= features.lighting_score <= 100.0
    assert 0.0 <= features.cctv_coverage_score <= 100.0
    assert features.historical_baseline >= 0.0
