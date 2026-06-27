import os
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

# Add the app directory to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.core import User, Provider, Bill, Payment, BillStatus, PaymentStatus
from app.database import SessionLocal

def seed_admin_bills():
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    # Fetch admin user Dolly
    dolly = db.query(User).filter(User.email == "dolly@gmail.com").first()

    if not dolly:
        print("Error: Could not find admin user Dolly in the database.")
        db.close()
        return

    # Fetch providers
    providers = {p.service_type: p for p in db.query(Provider).all()}

    # 10 new bills for Dolly (5 PAID, 3 PENDING, 2 OVERDUE)
    admin_bills_data = [
        # Paid
        {"provider": providers["Gas"], "amount": 550.00, "due": now - timedelta(days=15), "status": BillStatus.PAID, "paid": True},
        {"provider": providers["Water"], "amount": 250.00, "due": now - timedelta(days=22), "status": BillStatus.PAID, "paid": True},
        {"provider": providers["Internet"], "amount": 999.00, "due": now - timedelta(days=8), "status": BillStatus.PAID, "paid": True},
        {"provider": providers["Electricity"], "amount": 1150.00, "due": now - timedelta(days=3), "status": BillStatus.PAID, "paid": True},
        {"provider": providers["Maintenance"], "amount": 2000.00, "due": now - timedelta(days=18), "status": BillStatus.PAID, "paid": True},
        
        # Pending
        {"provider": providers["Gas"], "amount": 680.00, "due": now + timedelta(days=12), "status": BillStatus.PENDING, "paid": False},
        {"provider": providers["Water"], "amount": 320.00, "due": now + timedelta(days=16), "status": BillStatus.PENDING, "paid": False},
        {"provider": providers["Broadband"], "amount": 1050.00, "due": now + timedelta(days=22), "status": BillStatus.PENDING, "paid": False},
        
        # Overdue
        {"provider": providers["Electricity"], "amount": 1450.00, "due": now - timedelta(days=11), "status": BillStatus.OVERDUE, "paid": False},
        {"provider": providers["Property Tax"], "amount": 5000.00, "due": now - timedelta(days=4), "status": BillStatus.OVERDUE, "paid": False}
    ]

    print("Adding 10 more bills to admin user Dolly...")

    for i, data in enumerate(admin_bills_data):
        bill = Bill(
            user_id=dolly.id,
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
                user_id=dolly.id,
                amount_paid=data["amount"],
                penalty_amount=0.00,
                payment_method="CARD_VISA_****9999" if i % 2 == 0 else "UPI_admin_dolly@upi",
                transaction_id=f"TXN-ADMIN-MORE-{bill.id}",
                paid_at=data["due"] - timedelta(days=1),
                status=PaymentStatus.SUCCESS
            )
            db.add(payment)
            db.commit()

    print("Successfully added 10 new bills and 5 new payment records to Dolly!")
    db.close()

if __name__ == "__main__":
    seed_admin_bills()
