import httpx

# Verify the two winners and get their details
pairs = [
    ("Karol Bagh->Nehru Place", 77.1906, 28.6521, 77.2507, 28.5480),
    ("Paharganj->Dwarka Sec21", 77.2132, 28.6433, 77.0597, 28.5525),
]

for label, lon1, lat1, lon2, lat2 in pairs:
    url = f"https://router.project-osrm.org/route/v1/foot/{lon1},{lat1};{lon2},{lat2}?alternatives=3&steps=true&geometries=geojson&overview=full"
    r = httpx.get(url, timeout=15)
    data = r.json()
    routes = data.get("routes", [])
    print(f"\n{label}: {len(routes)} route(s)")
    for i, rt in enumerate(routes):
        print(f"  Route {i}: dist={rt['distance']:.0f}m  dur={rt['duration']:.0f}s  steps={len(rt['legs'][0]['steps'])}")
