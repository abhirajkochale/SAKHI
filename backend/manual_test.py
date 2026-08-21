import asyncio
from app.schemas.journey import JourneyRequest, Location
from app.services.routing.osrm_client import OSRMRoutingService

async def main():
    service = OSRMRoutingService()
    # Example coordinates: Churchgate to CST (approximate Mumbai coordinates)
    req = JourneyRequest(
        origin=Location(latitude=18.9322, longitude=72.8264),
        destination=Location(latitude=18.9398, longitude=72.8354)
    )
    print("Calling OSRM...")
    try:
        res = await service.get_journey(req)
        print("SUCCESS")
        print("Distance (m):", res.distance_m)
        print("Duration (s):", res.duration_s)
        print("Number of Segments:", len(res.segments))
        if res.segments:
            print("First Segment Sequence:", res.segments[0].sequence)
            print("First Segment Mode:", res.segments[0].mode)
            print("First Segment Geometry:", res.segments[0].geometry)
    except Exception as e:
        print("ERROR:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
