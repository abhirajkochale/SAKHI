import sys, os, urllib.request, json
sys.path.insert(0, '.')

from app.models.database import SessionLocal
from app.models.washroom import Washroom, WashroomFeedback

db = SessionLocal()
BASE = 'http://127.0.0.1:8000/api/v1'
COORDS = 'lat=28.6328&lon=77.2197'

print('1. Fetching washrooms...')
req = urllib.request.urlopen(f'{BASE}/osm-amenities/nearby?{COORDS}&category=washroom&radius_m=200')
data = json.loads(req.read())

print('2. Print IDs (Top 3)')
wA, wB, wC = data[0], data[1], data[2]
print(f"Washroom A: {wA['id']} | {wA['name']}")
print(f"Washroom B: {wB['id']} | {wB['name']}")
print(f"Washroom C: {wC['id']} | {wC['name']}")

print('\nSubmit Feedback A')
urllib.request.urlopen(urllib.request.Request(f'{BASE}/washrooms/{wA["id"]}/feedback', 
    data=json.dumps({"is_open":True,"cleanliness":"Clean","safety":"Safe","accessible":True}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}, method='POST'))

print('Submit Feedback B')
urllib.request.urlopen(urllib.request.Request(f'{BASE}/washrooms/{wB["id"]}/feedback', 
    data=json.dumps({"is_open":False,"cleanliness":"Dirty","safety":"Unsafe","accessible":False}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}, method='POST'))

print('Submit Feedback C')
urllib.request.urlopen(urllib.request.Request(f'{BASE}/washrooms/{wC["id"]}/feedback', 
    data=json.dumps({"is_open":True,"cleanliness":"Average","safety":"Concern","accessible":True}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}, method='POST'))

print('\nQuery DB for Feedback...')
fbs = db.query(WashroomFeedback).order_by(WashroomFeedback.timestamp.desc()).limit(3).all()
for f in fbs:
    print(f"Feedback ID: {f.id} | Washroom ID: {f.washroom_id} | Cleanliness: {f.cleanliness}")

print('\nFetch washrooms again and check fields...')
req2 = urllib.request.urlopen(f'{BASE}/osm-amenities/nearby?{COORDS}&category=washroom&radius_m=200')
data2 = json.loads(req2.read())
for i, w in enumerate(data2[:3]):
    print(f"Washroom {i+1}: ID={w['id']} | Cleanliness={w['cleanliness']} | Safety={w['safety']} | Rating={w['rating']}")

