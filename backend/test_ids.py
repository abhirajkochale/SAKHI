import sys, os, urllib.request, json
sys.path.insert(0, '.')

BASE = 'http://127.0.0.1:8000/api/v1'
COORDS = 'lat=28.6328&lon=77.2197'

req = urllib.request.urlopen(f'{BASE}/osm-amenities/nearby?{COORDS}&category=washroom&radius_m=200')
data = json.loads(req.read())

print(f'Total washrooms: {len(data)}')
for i, w in enumerate(data[:3]):
    print(f'Washroom {i+1}: {w["id"]} | {w["name"]} | Lat: {w["latitude"]} | Lon: {w["longitude"]}')

