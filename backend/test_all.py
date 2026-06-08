import requests, json

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODA1OTY3NDEsInN1YiI6IjUifQ.mglzG5SdBcmGazRrg6e5hHHWxlx8Xx8ZBnQaIShI7xU"
BASE = "http://localhost:8000/api/v1/messaging"
AUTH = {"Authorization": f"Bearer {TOKEN}"}

print("=== TEST 1: Send a message ===")
r = requests.post(f"{BASE}/messages/1", json={"content": "Hello! Testing direct messaging on OncoAI."}, headers=AUTH)
print(r.status_code, json.dumps(r.json(), indent=2))

print("\n=== TEST 2: Check conversations ===")
r = requests.get(f"{BASE}/messages/conversations", headers=AUTH)
print(r.status_code, json.dumps(r.json(), indent=2))

print("\n=== TEST 3: Email test ===")
r = requests.post(f"{BASE}/email/test", json={
    "email": "ace.anmol.srivastava@gmail.com",
    "subject": "OncoAI Email Working",
    "body": "If you see this, the OncoAI email notification system is active. You will receive emails when users are banned."
}, headers=AUTH)
print(r.status_code, json.dumps(r.json(), indent=2))

print("\n=== TEST 4: Doctor Verification ===")
r = requests.post(f"{BASE}/doctors/1/verify", json={"doctor_id": 1, "is_verified": True}, headers=AUTH)
print(r.status_code, json.dumps(r.json(), indent=2))
