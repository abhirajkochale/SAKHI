import sys, os, urllib.request, json
sys.path.insert(0, '.')

from app.models.database import SessionLocal
from app.models.washroom import Washroom, WashroomFeedback
import urllib.error

db = SessionLocal()

print('=== 1. WASHROOM TABLE ===')
ws = db.query(Washroom).all()
print(f'Total rows: {len(ws)}')
print('3 Example Geoapify Washrooms:')
for w in ws[:3]:
    print(f'  - PK/External ID: {w.id} | Name: {w.name}')

print('\n=== 2. WASHROOM_FEEDBACK TABLE ===')
fb = db.query(WashroomFeedback).order_by(WashroomFeedback.timestamp.desc()).all()
print(f'Total rows: {len(fb)}')
print('Latest 5 feedbacks:')
for f in fb[:5]:
    exists = any(w.id == f.washroom_id for w in ws)
    print(f'  - Feedback ID: {f.id} | Washroom ID: {f.washroom_id} | FK Valid: {exists}')

print('\n=== 3, 4, 5. ENDPOINT & FEEDBACK TEST ===')
BASE = 'http://127.0.0.1:8000/api/v1'
COORDS = 'lat=28.6328&lon=77.2197&radius_m=1000'

req = urllib.request.urlopen(f'{BASE}/osm-amenities/nearby?{COORDS}&category=washroom')
data = json.loads(req.read())

target_w = data[0]
w_id = target_w['id']
print(f'Selected Washroom: {target_w["name"]} (ID: {w_id})')
print(f'Before Feedback -> Rating: {target_w.get("rating")}, Count: {target_w.get("rating_count")}')

print(f'\nSubmitting POST /washrooms/{w_id}/feedback...')
payload = json.dumps({
    "is_open": True,
    "cleanliness": "Clean",
    "safety": "Safe",
    "accessible": True
}).encode('utf-8')

req2 = urllib.request.Request(f'{BASE}/washrooms/{w_id}/feedback', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
res2 = urllib.request.urlopen(req2)
print("Submit Response:", res2.read().decode())

new_fb = db.query(WashroomFeedback).filter(WashroomFeedback.washroom_id == w_id).order_by(WashroomFeedback.timestamp.desc()).first()
print(f'DB Verification -> Found new feedback row ID: {new_fb.id} at {new_fb.timestamp}')

req3 = urllib.request.urlopen(f'{BASE}/osm-amenities/nearby?{COORDS}&category=washroom')
data3 = json.loads(req3.read())
updated_w = [d for d in data3 if d['id'] == w_id][0]
print(f'After Feedback -> Rating: {updated_w.get("rating")}, Count: {updated_w.get("rating_count")}')

print('\n=== 7. DUPLICATE CHECK ===')
ws_after = db.query(Washroom).all()
print(f'Washroom DB rows before second search: {len(ws)}')
print(f'Washroom DB rows after second search: {len(ws_after)}')
if len(ws) == len(ws_after):
    print('No duplicate washroom rows were created.')

