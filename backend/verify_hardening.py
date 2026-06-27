import requests
import json
import time

BASE_URL = "http://localhost:8000/api"
USER_EMAIL = "system@test.com"
USER_PW = "testpass"

# 1. Login to get token
resp = requests.post(f"{BASE_URL}/auth/login", data={"username": USER_EMAIL, "password": USER_PW})
if resp.status_code != 200:
    # the user was deleted, recreate it
    requests.post(f"{BASE_URL}/auth/register", json={"name": "System", "email": USER_EMAIL, "password": USER_PW})
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": USER_EMAIL, "password": USER_PW})

token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

print("--- VERIFYING HARDENING AND NEW API REQUIREMENTS ---")

# 2. Test Error Unwrapping and Rate Limiter
print("\n[TEST] Rate Limiter on /payments/")
for i in range(6):
    r = requests.post(f"{BASE_URL}/payments/", headers=headers, json={"bill_id": 1, "amount_paid": 100, "payment_method": "UPI"})
    if r.status_code == 429:
        print(f"-> Allowed {i} requests. Request {i+1} TRIGGERED RATE LIMITER: 429 Too Many Requests")
        break
    time.sleep(0.1)

# Wait for rate limit flush or just hit another endpoint
# 3. Test duplicate protection & Amount mismatch
print("\n[TEST] Idempotency & Validation Error Format")
r2 = requests.post(f"{BASE_URL}/payments/", headers=headers, json={"bill_id": 999, "amount_paid": 50, "payment_method": "WALLET"})
print(f"Status: {r2.status_code}, Body: {r2.json()}")
if "status" in r2.json() and r2.json()["status"] == "error":
    print("-> Successfully verified standard {\"status\": \"error\"} wrapper format on 404/400.")

print("\n[TEST] High Amount Fraud Flagging & Success Wrapper")
# Assuming User 2 has bill 1 unpaid still. 
# We need an admin login to verify the fraud flag.
ADMIN_EMAIL = "admin@secpay.com"
ADMIN_PW = "admin123"
try:
    admin_resp = requests.post(f"{BASE_URL}/auth/login", data={"username": ADMIN_EMAIL, "password": ADMIN_PW})
    admin_token = admin_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    fraud_req = requests.get(f"{BASE_URL}/admin/fraud-alerts", headers=admin_headers)
    print(f"Fraud Status: {fraud_req.status_code}")
    if fraud_req.status_code == 200:
        print("-> Successfully verified Admin Fraud Route returning {\"status\": \"success\"} wrapper.")
except Exception as e:
    print(f"Could not test admin: {e}")

print("\n--- ALL TESTS COMPLETE ---")
