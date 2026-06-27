import urllib.request as r
from urllib.error import HTTPError

req = r.Request(
    'http://127.0.0.1:8000/api/auth/register',
    data=b'{"name": "test3", "email": "test3@g.com", "password": "pwd"}',
    method='POST',
    headers={'Content-Type': 'application/json'}
)

try:
    print(r.urlopen(req).read().decode())
except HTTPError as e:
    print("HTTP ERROR CODE:", e.code)
    print("ERROR BODY:", e.read().decode())
