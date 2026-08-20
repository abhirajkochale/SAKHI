import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.emergency import SOSRequest, SOSResponse, CheckinRequest, CheckinResponse, DeadManEvent

# In-memory storage for prototype
_sos_events: Dict[str, SOSResponse] = {}
_dead_man_events: Dict[str, DeadManEvent] = {}
_checkins: Dict[str, dict] = {} # journey_id -> {"last_seen_at": datetime, "timeout_minutes": int, "location": dict}

class EmergencyService:
    def trigger_sos(self, request: SOSRequest) -> SOSResponse:
        sos_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        response = SOSResponse(
            status="triggered",
            sos_id=sos_id,
            message="SOS event recorded. (Prototype: No external service contacted)",
            location={"latitude": request.latitude, "longitude": request.longitude},
            journey_id=request.journey_id,
            trigger_source=request.trigger_source,
            triggered_at=now
        )
        
        _sos_events[sos_id] = response
        print(f"[EMERGENCY] SOS Triggered: {request.trigger_source} at {request.latitude}, {request.longitude}")
        return response

    def record_checkin(self, journey_id: str, request: CheckinRequest) -> CheckinResponse:
        now = datetime.now(timezone.utc)
        timeout_minutes = 5 # Default 5 mins for prototype
        
        _checkins[journey_id] = {
            "last_seen_at": now,
            "timeout_minutes": timeout_minutes,
            "location": {"latitude": request.latitude, "longitude": request.longitude} if request.latitude and request.longitude else None
        }
        
        # Calculate next deadline (naive approach for prototype)
        import timedelta
        from datetime import timedelta
        deadline = now + timedelta(minutes=timeout_minutes)
        
        return CheckinResponse(
            status="checked_in",
            journey_id=journey_id,
            checked_in_at=now,
            next_checkin_deadline=deadline,
            timeout_minutes=timeout_minutes
        )
        
    def check_dead_man_timeouts(self) -> List[DeadManEvent]:
        """Called periodically or manually to check for missed check-ins."""
        now = datetime.now(timezone.utc)
        new_events = []
        
        for journey_id, data in list(_checkins.items()):
            last_seen = data["last_seen_at"]
            timeout = data["timeout_minutes"]
            from datetime import timedelta
            deadline = last_seen + timedelta(minutes=timeout)
            
            if now > deadline:
                # Timeout occurred!
                event = DeadManEvent(
                    journey_id=journey_id,
                    last_seen_at=last_seen,
                    timeout_minutes=timeout,
                    location=data.get("location"),
                    auto_sos_triggered=True
                )
                _dead_man_events[journey_id] = event
                
                # Auto trigger SOS
                loc = data.get("location") or {"latitude": 0.0, "longitude": 0.0}
                sos_req = SOSRequest(
                    journey_id=journey_id,
                    latitude=loc.get("latitude", 0.0),
                    longitude=loc.get("longitude", 0.0),
                    trigger_source="dead_man_switch"
                )
                self.trigger_sos(sos_req)
                
                # Remove from active checkins so we don't trigger repeatedly
                del _checkins[journey_id]
                new_events.append(event)
                
        return new_events
        
    def get_all_sos_events(self) -> List[SOSResponse]:
        return list(_sos_events.values())

def get_emergency_service() -> EmergencyService:
    return EmergencyService()
