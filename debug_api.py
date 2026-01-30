import requests
import json
try:
    r = requests.get("http://localhost:8000/api/v1/map/positions")
    data = r.json()
    print(f"Count: {len(data)}")
    ids = set(d['device_id'] for d in data)
    print(f"IDs: {ids}")
except Exception as e:
    print(e)
