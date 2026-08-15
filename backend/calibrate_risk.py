"""
Calibration script: find context values that hit target risk ranges.
Run: python calibrate_risk.py
"""
import sys
sys.path.insert(0, ".")
from datetime import datetime
from app.schemas.journey import JourneySegment, Location
from app.schemas.risk import SegmentContext
from app.services.risk.risk_service import RiskService

svc = RiskService()

def probe(label, footfall, validated, infra, cctv, police, transit, baseline):
    seg = JourneySegment(
        segment_id="test", journey_id="j", sequence=1, mode="walking",
        start_location=Location(latitude=28.6433, longitude=77.2132),
        end_location=Location(latitude=28.5525, longitude=77.0597),
        distance_m=1000, duration_s=720,
        geometry={"type": "LineString", "coordinates": [[77.2132, 28.6433], [77.0597, 28.5525]]}
    )
    ctx = SegmentContext(
        departure_time=datetime.now(),
        footfall_indicator=footfall,
        validated_report_signal=validated,
        infrastructure_score=infra,
        cctv_coverage=cctv,
        police_proximity=police,
        transit_access=transit,
        historical_baseline=baseline,
    )
    r = svc.calculate_risk(seg, ctx)
    print(f"{label:35s} -> risk={r.risk_score:.1f}  conf={r.confidence_score:.1f}")

print("\n--- Mumbai Safest (target 20-30) ---")
probe("mu_safe", footfall=0.50, validated=0.50, infra=0.45, cctv=0.45, police=0.35, transit=0.45, baseline=0.50)

print("\n--- Mumbai Fastest (target 50-60) ---")
probe("mu_fast", footfall=0.15, validated=0.75, infra=0.25, cctv=0.30, police=0.20, transit=0.30, baseline=0.75)

print("\n--- Delhi Safest (target 45-50) ---")
probe("dl_safe", footfall=0.20, validated=0.65, infra=0.30, cctv=0.35, police=0.25, transit=0.35, baseline=0.65)

print("\n--- Delhi Fastest (target 70-80) ---")
probe("dl_fast", footfall=0.00, validated=1.00, infra=0.05, cctv=0.15, police=0.05, transit=0.15, baseline=0.90)

