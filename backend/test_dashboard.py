import requests
from datetime import datetime, timedelta

def seed_bills(user_id):
    from app.database import SessionLocal
    from app.models import core
    session = SessionLocal()
    bills = session.query(core.Bill).filter_by(user_id=user_id).all()
    if not bills:
        print(f"Adding mock bills to MySQL for user {user_id}...")
        for i in range(1, 4):
            b = core.Bill(
                user_id=user_id,
                provider_id=1,
                amount=100.0 * i,
                due_date=datetime.utcnow() - timedelta(days=i),  # Overdue
                status=core.BillStatus.PENDING
            )
            session.add(b)
        session.commit()
    session.close()

def test():
    try:
        # 1. Login
        login_resp = requests.post(
            'http://localhost:8000/api/auth/login', 
            data={'username': 'alice@example.com', 'password': 'password123'}
        )
        print("Login status:", login_resp.status_code)
        
        import base64
        import json
        
        token = login_resp.json().get('access_token')
        
        # Decode JWT payload
        payload_b64 = token.split('.')[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4) 
        payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
        
        user_id = payload.get('user_id')
        
        if not token or not user_id:
            print("Failed to get token or user_id:", login_resp.text)
            return
            
        print(f"Logged in as User ID: {user_id}")
        
        # 2. Add Bills dynamically
        seed_bills(user_id)
            
        # 3. Get Dashboard
        headers = {'Authorization': f'Bearer {token}'}
        dash_resp = requests.get(f'http://localhost:8000/api/dashboard/{user_id}', headers=headers)
        
        print(f"Dashboard status code: {dash_resp.status_code}")
        print(f"Dashboard response: {dash_resp.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test()
