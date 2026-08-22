import asyncio
import os
import uuid
import sys
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.connection import get_db
from app.core.config import settings
from app.services.emergency.emergency_service import get_emergency_service
from app.schemas.emergency import SOSRequest, CheckinRequest
from app.services.context_update_service import ContextUpdateService
from app.schemas.context import ContextUpdateEvent
from app.services.risk.segment_lookup_service import get_segment_lookup_service

async def run_tests():
    print("--- 1. Testing Database Connection ---")
    db = await get_db()
    try:
        await db.execute("SELECT 1")
        print("Database connection: SUCCESS")
    except Exception as e:
        print(f"Database connection: FAILED - {e}")
        return

    print("\n--- 2. Testing spatial_amenities read ---")
    try:
        amenities = await get_segment_lookup_service().get_public_toilets()
        print(f"spatial_amenities read: SUCCESS (Found {len(amenities)} records)")
    except Exception as e:
        print(f"spatial_amenities read: FAILED - {e}")

    # Set up test data
    test_journey_id = str(uuid.uuid4())
    test_sos_id = None
    
    print("\n--- 3. Testing active_journeys persistence ---")
    try:
        await db.execute(
            """
            INSERT INTO active_journeys (id, origin_lat, origin_lon, dest_lat, dest_lon, status)
            VALUES ($1, $2, $3, $4, $5, 'active')
            """,
            test_journey_id, 28.6, 77.2, 28.7, 77.3
        )
        print("active_journeys create: SUCCESS")
        
        # Test record_checkin (updates last_checkin_at)
        emergency_svc = get_emergency_service()
        req = CheckinRequest(latitude=28.65, longitude=77.25)
        await emergency_svc.record_checkin(test_journey_id, req)
        
        row = await db.fetchrow("SELECT last_checkin_at FROM active_journeys WHERE id = $1", test_journey_id)
        if row and row['last_checkin_at']:
            print("active_journeys update (checkin): SUCCESS")
        else:
            print("active_journeys update (checkin): FAILED - last_checkin_at not set")
    except Exception as e:
        print(f"active_journeys test: FAILED - {e}")

    print("\n--- 4. Testing emergency_events persistence ---")
    try:
        req = SOSRequest(journey_id=test_journey_id, latitude=28.65, longitude=77.25, trigger_source="manual")
        sos_res = await emergency_svc.trigger_sos(req)
        test_sos_id = sos_res.sos_id
        
        row = await db.fetchrow("SELECT id, ST_AsText(geom) as geom FROM emergency_events WHERE id = $1", test_sos_id)
        if row and row['geom']:
            print("emergency_events create: SUCCESS (geom auto-generated via trigger)")
        else:
            print("emergency_events create: FAILED - record or geom missing")
    except Exception as e:
        print(f"emergency_events test: FAILED - {e}")

    print("\n--- 5. Testing safety_reports persistence ---")
    try:
        # Note: ContextUpdateService process_update is heavily tied to in-memory journey_store candidates.
        # We can just directly invoke the DB logic to test persistence, since process_update requires a full valid journey.
        report_id = str(uuid.uuid4())
        await db.execute(
            """
            INSERT INTO safety_reports (id, event_type, severity, latitude, longitude, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            report_id, 'validated_report', 80, 28.65, 77.25, datetime.now(timezone.utc)
        )
        row = await db.fetchrow("SELECT id, ST_AsText(geom) as geom FROM safety_reports WHERE id = $1", report_id)
        if row and row['geom']:
            print("safety_reports create: SUCCESS (geom auto-generated)")
            await db.execute("DELETE FROM safety_reports WHERE id = $1", report_id)
        else:
            print("safety_reports create: FAILED")
    except Exception as e:
        print(f"safety_reports test: FAILED - {e}")

    print("\n--- 6. Cleaning up test data ---")
    try:
        # Delete journey (should cascade to emergency_events due to ON DELETE SET NULL, 
        # or we explicitly delete emergency_events if needed. The schema says ON DELETE SET NULL for journey_id, 
        # so emergency_event will still exist. We must delete it.)
        if test_sos_id:
            await db.execute("DELETE FROM emergency_events WHERE id = $1", test_sos_id)
        await db.execute("DELETE FROM active_journeys WHERE id = $1", test_journey_id)
        print("Cleanup: SUCCESS")
    except Exception as e:
        print(f"Cleanup: FAILED - {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())
