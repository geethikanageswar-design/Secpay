import os
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

# Add the app directory to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.core import User, Provider, Bill, Payment, BillStatus, PaymentStatus
from app.database import SessionLocal

def seed_more_bills():
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    # Fetch users
    dolly = db.query(User).filter(User.email == "dolly@gmail.com").first()
    john = db.query(User).filter(User.email == "john@example.com").first()
    jane = db.query(User).filter(User.email == "jane@example.com").first()

    if not all([dolly, john, jane]):
        print("Error: Could not find dolly, john, or jane in the database. Please seed users first.")
        db.close()
        return

    # Fetch providers
    providers = {p.service_type: p for p in db.query(Provider).all()}

    # New bills definition (9 PAID, 2 PENDING, 1 OVERDUE)
    new_bills_data = [
        # --- Dolly ---
        {"user_id": dolly.id, "provider": providers["Gas"], "amount": 800.00, "due": now - timedelta(days=6), "status": BillStatus.PAID, "paid": True},
        {"user_id": dolly.id, "provider": providers["Broadband"], "amount": 1100.00, "due": now - timedelta(days=2), "status": BillStatus.PAID, "paid": True},
        {"user_id": dolly.id, "provider": providers["Property Tax"], "amount": 5000.00, "due": now - timedelta(days=12), "status": BillStatus.PAID, "paid": True},
        {"user_id": dolly.id, "provider": providers["Electricity"], "amount": 1300.00, "due": now + timedelta(days=20), "status": BillStatus.PENDING, "paid": False},

        # --- John Doe ---
        {"user_id": john.id, "provider": providers["Water"], "amount": 300.00, "due": now - timedelta(days=14), "status": BillStatus.PAID, "paid": True},
        {"user_id": john.id, "provider": providers["Broadband"], "amount": 1200.00, "due": now - timedelta(days=4), "status": BillStatus.PAID, "paid": True},
        {"user_id": john.id, "provider": providers["Maintenance"], "amount": 2500.00, "due": now - timedelta(days=10), "status": BillStatus.PAID, "paid": True},
        {"user_id": john.id, "provider": providers["Gas"], "amount": 700.00, "due": now + timedelta(days=18), "status": BillStatus.PENDING, "paid": False},

        # --- Jane Smith ---
        {"user_id": jane.id, "provider": providers["Electricity"], "amount": 1450.00, "due": now - timedelta(days=15), "status": BillStatus.PAID, "paid": True},
        {"user_id": jane.id, "provider": providers["Internet"], "amount": 999.00, "due": now - timedelta(days=9), "status": BillStatus.PAID, "paid": True},
        {"user_id": jane.id, "provider": providers["Maintenance"], "amount": 2200.00, "due": now - timedelta(days=3), "status": BillStatus.PAID, "paid": True},
        {"user_id": jane.id, "provider": providers["Gas"], "amount": 880.00, "due": now - timedelta(days=10), "status": BillStatus.OVERDUE, "paid": False}
    ]

    print("Adding 12 additional bills to database...")

    for i, data in enumerate(new_bills_data):
        bill = Bill(
            user_id=data["user_id"],
            provider_id=data["provider"].id,
            amount=data["amount"],
            due_date=data["due"],
            status=data["status"],
            created_at=data["due"] - timedelta(days=20)
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)

        if data["paid"]:
            payment = Payment(
                bill_id=bill.id,
                user_id=data["user_id"],
                amount_paid=data["amount"],
                penalty_amount=0.00,
                payment_method="CARD_VISA_****5555" if i % 2 == 0 else "UPI_more_demo@upi",
                transaction_id=f"TXN-ADDITIONAL-{data['user_id']}-{bill.id}",
                paid_at=data["due"] - timedelta(days=1),
                status=PaymentStatus.SUCCESS
            )
            db.add(payment)
            db.commit()

    print("Successfully added 12 new bills and 9 new payment records!")
    db.close()

if __name__ == "__main__":
    seed_more_bills()
