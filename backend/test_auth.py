import urllib.request
import json
import traceback

def test_endpoint(url, data, is_json=True):
    print(f"\n--- Testing {url} ---")
    headers = {
        "Origin": "http://localhost:3000"
    }
    if is_json:
        data_encoded = json.dumps(data).encode('utf-8')
        headers["Content-Type"] = "application/json"
    else:
        # form encoded
        from urllib.parse import urlencode
        data_encoded = urlencode(data).encode('utf-8')
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, data=data_encoded, headers=headers, method="POST")
    token = None
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Status: {resp.status}")
            resp_body = resp.read().decode()
            print("Response:", resp_body)
            if "access_token" in resp_body:
                token = json.loads(resp_body).get("access_token")
            print("Headers:")
            for k, v in resp.headers.items():
                if "access" in k.lower() or k.lower() == "content-type":
                    print(f"  {k}: {v}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print("Response:", e.read().decode())
        print("Headers:")
        for k, v in e.headers.items():
            if "access" in k.lower() or k.lower() == "content-type":
                print(f"  {k}: {v}")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        
    return token

test_endpoint("http://localhost:8000/api/auth/register", {"name": "Test User", "email": "test@test.com", "password": "password"}, True)
token = test_endpoint("http://localhost:8000/api/auth/login", {"username": "test@test.com", "password": "password"}, False)

if token:
    print(f"\n--- Testing http://localhost:8000/api/bills/user/3 ---")
    headers = {
        "Origin": "http://localhost:3000",
        "Authorization": f"Bearer {token}"
    }
    req = urllib.request.Request("http://localhost:8000/api/bills/user/3", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Status: {resp.status}")
            print("Response:", resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print("Response:", e.read().decode())
