import urllib.request
req = urllib.request.Request("http://localhost:8000/api/auth/login", method="OPTIONS")
req.add_header("Origin", "http://localhost:3000")
req.add_header("Access-Control-Request-Method", "POST")
try:
    with urllib.request.urlopen(req) as resp:
        print(f"Status: {resp.status}")
        print("Headers:")
        for k, v in resp.headers.items():
            print(f"{k}: {v}")
except Exception as e:
    print(f"Error: {e}")
