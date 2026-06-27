import requests
import json

def test_payment():
    try:
        print("--- 1. Login ---")
        login_resp = requests.post(
            'http://localhost:8000/api/auth/login', 
            data={'username': 'alice@example.com', 'password': 'password123'}
        )
        token = login_resp.json().get('access_token')
        
        import base64
        payload_b64 = token.split('.')[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4) 
        payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
        user_id = payload.get('user_id')
        print(f"Token acquired. User ID: {user_id}")
        
        headers = {'Authorization': f'Bearer {token}'}
        
        print("\n--- 2. Get Bills ---")
        bills_resp = requests.get(f'http://localhost:8000/api/dashboard/{user_id}', headers=headers)
        bills_data = bills_resp.json()
        print("Dashboard Data:", bills_data)
        
        # We know Alice has 3 mock bills. Let's get the raw list of bills to find a bill ID
        raw_bills_resp = requests.get(f'http://localhost:8000/api/bills/user/{user_id}', headers=headers)
        raw_bills = raw_bills_resp.json().get('data', [])
        
        if not raw_bills:
            print("No bills found for Alice.")
            return

        target_bill = raw_bills[0]
        bill_id = target_bill['id']
        amount = target_bill['amount']
        
        # Calculate expected penalty
        expected_total = amount
        if target_bill['status'] == 'OVERDUE':
            expected_total = amount * 1.02
        
        print(f"\nTargeting Bill ID: {bill_id}")
        print(f"Base Amount: {amount}")
        print(f"Expected Payment Amount (with penalty): {expected_total}")
        
        print("\n--- 3. Make Payment ---")
        payment_payload = {
            "bill_id": bill_id,
            "amount_paid": expected_total,
            "payment_method": "CARD",
            "cardholder_name": "Test User",
            "card_number": "1234567890128",
            "expiry_date": "12/28",
            "cvv": "123"
        }
        
        pay_resp = requests.post(
            'http://localhost:8000/api/payments/', 
            json=payment_payload,
            headers=headers
        )
        print(f"Payment Status: {pay_resp.status_code}")
        print(f"Payment Response: {pay_resp.text}")
        
        print("\n--- 4. Verify Payment History ---")
        history_resp = requests.get('http://localhost:8000/api/payments/history', headers=headers)
        print(f"History Status: {history_resp.status_code}")
        print(f"History Data: {history_resp.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_payment()
