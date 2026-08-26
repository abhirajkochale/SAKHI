import sys, os, urllib.request, json
sys.path.insert(0, '.')

BASE = 'http://127.0.0.1:8000/api/v1'
COORDS = 'lat=28.6328&lon=77.2197'

req = urllib.request.urlopen(f'{BASE}/osm-amenities/nearby?{COORDS}&category=washroom&radius_m=200')
data = json.loads(req.read())

for w in data:
    print(f"ID: {w['id']} | Rating: {w.get('rating')} ({w.get('rating_count')})")

