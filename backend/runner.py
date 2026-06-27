import subprocess
import time
import urllib.request as r
from urllib.error import HTTPError

print("Starting server...")
proc = subprocess.Popen([r'.\venv\Scripts\uvicorn.exe', 'main:app', '--port', '8001'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
time.sleep(3)

print("Making request...")
req = r.Request(
    'http://127.0.0.1:8001/api/auth/register',
    data=b'{"name": "test4", "email": "test4@g.com", "password": "pwd"}',
    method='POST',
    headers={'Content-Type': 'application/json'}
)

try:
    print(r.urlopen(req).read().decode())
except HTTPError as e:
    print("HTTP ERROR CODE:", e.code)
    print("ERROR BODY:", e.read().decode())
except Exception as e:
    print("OTHER ERROR:", e)

proc.terminate()
stdout, stderr = proc.communicate()

print("\n--- Uvicorn STDOUT ---")
print(stdout)
print("\n--- Uvicorn STDERR ---")
print(stderr)
