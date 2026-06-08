import requests

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODA1OTY3NDEsInN1YiI6IjUifQ.mglzG5SdBcmGazRrg6e5hHHWxlx8Xx8ZBnQaIShI7xU"

r = requests.post("http://localhost:8000/api/v1/messaging/email/test",
    json={"email": "anmol.srivastava.dev@gmail.com",
          "subject": "OncoAI Email Working",
          "body": "If you see this, the OncoAI email notification system is active."},
    headers={"Authorization": f"Bearer {TOKEN}"})
print(r.json())
