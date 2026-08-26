import sys, os, urllib.request, json
sys.path.insert(0, '.')

from app.models.database import SessionLocal
from app.models.washroom import Washroom, WashroomFeedback
import urllib.error
from datetime import datetime

db = SessionLocal()

print('=== TEST 2: JOURNEY MAP RADIUS (200m) ===')
BASE = 'http://127.0.0.1:8000/api/v1'
COORDS = 'lat=28.6328&lon=77.2197'

try:
    req_j = urllib.request.urlopen(f'{BASE}/osm-amenities/nearby?{COORDS}&category=washroom&radius_m=200')
    data_j = json.loads(req_j.read())
    print(f'Found {len(data_j)} washrooms within 200m.')
    for w in data_j:
        print(f"  - {w['name']} ({w['distance_m']}m)")
except Exception as e:
    print('Error:', e)

print('\n=== TEST 3: QUICK ACTIONS RADIUS (1000m) ===')
try:
    req_q = urllib.request.urlopen(f'{BASE}/osm-amenities/nearby?{COORDS}&category=washroom&radius_m=1000')
    data_q = json.loads(req_q.read())
    print(f'Found {len(data_q)} washrooms within 1000m.')
except Exception as e:
    print('Error:', e)

print('\n=== TEST 4: FEEDBACK DATABASE SEPARATION ===')
if len(data_j) >= 2:
    wA = data_j[0]
    wB = data_j[1]
    print(f'Washroom A: {wA["id"]}')
    print(f'Washroom B: {wB["id"]}')
    
    # Submit A
    reqA = urllib.request.Request(f'{BASE}/washrooms/{wA["id"]}/feedback', 
                                data=json.dumps({"is_open":True,"cleanliness":"Clean","safety":"Safe","accessible":True}).encode('utf-8'),
                                headers={'Content-Type': 'application/json'}, method='POST')
    urllib.request.urlopen(reqA)
    
    # Submit B
    reqB = urllib.request.Request(f'{BASE}/washrooms/{wB["id"]}/feedback', 
                                data=json.dumps({"is_open":True,"cleanliness":"Average","safety":"Concern","accessible":False}).encode('utf-8'),
                                headers={'Content-Type': 'application/json'}, method='POST')
    urllib.request.urlopen(reqB)
    
    # Verify DB
    fb_all = db.query(WashroomFeedback).order_by(WashroomFeedback.timestamp.desc()).limit(2).all()
    print('Latest 2 feedbacks:')
    for f in fb_all:
        print(f'  - Feedback ID: {f.id} | Washroom ID: {f.washroom_id} | Cleanliness: {f.cleanliness}')

