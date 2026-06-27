import os
import sys
from datetime import datetime, timedelta, timezone
import uuid

# Add the parent directory to sys.path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.core import User, Provider, Bill, Payment, BillStatus, PaymentStatus

def seed_demo_data():
    db: Session = SessionLocal()
    try:
        # 1. Get Alice
        alice = db.query(User).filter(User.email == "alice@example.com").first()
        if not alice:
            print("Alice not found! Please run the registration script first.")
            return

        print(f"Found user: {alice.name} (ID: {alice.id})")

        # 2. Clear existing bills and payments for Alice
        db.query(Payment).filter(Payment.user_id == alice.id).delete()
        db.query(Bill).filter(Bill.user_id == alice.id).delete()
        db.commit()
        print("Cleared existing bills and payments for Alice.")

        # 3. Ensure Providers Exist
        provider_data = [
            {"name": "TSSPDCL Electricity", "service_type": "Electricity"},
            {"name": "Hyderabad Water Board", "service_type": "Water"},
            {"name": "ACT Fibernet", "service_type": "Internet"}
        ]
        
        providers = {}
        for pdata in provider_data:
            prov = db.query(Provider).filter(Provider.name == pdata["name"]).first()
            if not prov:
                prov = Provider(**pdata)
                db.add(prov)
                db.commit()
                db.refresh(prov)
            providers[pdata["service_type"]] = prov
            
        print("Providers ensured.")

        # 4. Create 12 Bills (4 per provider)
        # Amounts: 850, 1450, 3200, 2750, 610, 980, 4300, 1200, 760, 1500, 2100, 540
        # Target: 5 PENDING, 3 OVERDUE, 4 PAID
        
        now = datetime.now(timezone.utc)
        
        bills_to_create = [
            # Electricity (1 OVERDUE, 2 PENDING, 1 PAID)
            {"type": "Electricity", "amount": 1450.00, "status": BillStatus.OVERDUE, "due_date": now - timedelta(days=45)}, # Overdue from Jan (approx)
            {"type": "Electricity", "amount": 1200.00, "status": BillStatus.PENDING, "due_date": now + timedelta(days=12)},
            {"type": "Electricity", "amount": 850.00,  "status": BillStatus.PENDING, "due_date": now + timedelta(days=2)},
            {"type": "Electricity", "amount": 3200.00, "status": BillStatus.PAID,    "due_date": now - timedelta(days=15)}, # Paid already

            # Water (1 OVERDUE, 2 PENDING, 1 PAID)
            {"type": "Water", "amount": 540.00, "status": BillStatus.OVERDUE, "due_date": now - timedelta(days=10)},
            {"type": "Water", "amount": 610.00, "status": BillStatus.PENDING, "due_date": now + timedelta(days=7)},
            {"type": "Water", "amount": 760.00, "status": BillStatus.PENDING, "due_date": now + timedelta(days=20)},
            {"type": "Water", "amount": 980.00, "status": BillStatus.PAID,    "due_date": now - timedelta(days=40)},

            # Internet (1 OVERDUE, 1 PENDING, 2 PAID)
            {"type": "Internet", "amount": 2750.00, "status": BillStatus.OVERDUE, "due_date": now - timedelta(days=5)},
            {"type": "Internet", "amount": 1500.00, "status": BillStatus.PENDING, "due_date": now + timedelta(days=10)},
            {"type": "Internet", "amount": 2100.00, "status": BillStatus.PAID,    "due_date": now - timedelta(days=30)},
            {"type": "Internet", "amount": 4300.00, "status": BillStatus.PAID,    "due_date": now - timedelta(days=60)},
        ]

        created_bills = []
        for bdata in bills_to_create:
            bill = Bill(
                user_id=alice.id,
                provider_id=providers[bdata["type"]].id,
                amount=bdata["amount"],
                due_date=bdata["due_date"].replace(tzinfo=None),
                status=bdata["status"]
            )
            db.add(bill)
            db.commit()
            db.refresh(bill)
            created_bills.append(bill)

        print("Created 12 bills.")

        # 5. Create Payment Records for the PAID bills
        for bill in created_bills:
            if bill.status == BillStatus.PAID:
                # Paid fully, generally before due date or on due date
                paid_time = bill.due_date - timedelta(days=2) 
                tx_id = f"TXN-{uuid.uuid4().hex.upper()}"
                payment = Payment(
                    bill_id=bill.id,
                    user_id=alice.id,
                    amount_paid=bill.amount,
                    penalty_amount=0.00,
                    payment_method="CARD_****1234",
                    transaction_id=tx_id,
                    status=PaymentStatus.SUCCESS,
                    fraud_flag=False,
                    paid_at=paid_time
                )
                db.add(payment)
                
        db.commit()
        print("Created corresponding payment records for PAID bills.")
        print("Demo data seeding complete!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
