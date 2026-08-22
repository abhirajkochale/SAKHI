import urllib.request
import json
import ssl

def fetch(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        req.data = json.dumps(data).encode()
        req.add_header('Content-Type', 'application/json')
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx) as response:
        return json.loads(response.read().decode())

try:
    print("Fetching washrooms...")
    washrooms = fetch('http://localhost:8000/api/v1/washrooms?latitude=28.6139&longitude=77.2090')
    print("Washrooms found:", len(washrooms))
    if washrooms:
        wid = washrooms[0]['id']
        print(f"Submitting feedback for washroom {wid}...")
        res = fetch(f'http://localhost:8000/api/v1/washrooms/{wid}/feedback', method='POST', data={
            "is_open": True,
            "cleanliness": "Clean",
            "safety": "Safe",
            "accessible": True
        })
        print("Feedback response:", res)
        print("Refetching washrooms...")
        washrooms = fetch('http://localhost:8000/api/v1/washrooms?latitude=28.6139&longitude=77.2090')
        print("Updated washroom:", washrooms[0])
except Exception as e:
    import traceback
    traceback.print_exc()
