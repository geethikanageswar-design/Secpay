import os
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.core import User, Provider, Bill, Payment, BillStatus, PaymentStatus, UserRole
from app.database import SessionLocal
from app.utils.security import get_password_hash

# Connect to database
db = SessionLocal()

def seed_demo_data():
    now = datetime.now(timezone.utc)
    
    # Ensure users 4 and 5 exist
    for user_id in [4, 5]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"Creating user {user_id}")
            user = User(
                id=user_id,
                name=f"Demo User {user_id}",
                email=f"demo{user_id}@example.com",
                password_hash=get_password_hash("password123"), # So recruiters can login
                role=UserRole.USER
            )
            db.add(user)
        else:
            # Update password if already exists
            user.password_hash = get_password_hash("password123")
            
    db.commit()

    # Define Providers
    provider_names = [
        ("PowerGrid Corp", "Electricity"),
        ("Aqua Flow Utilities", "Water"),
        ("EcoGas Solutions", "Gas"),
        ("FiberNet Xtreme", "Internet"),
        ("Sky Fiber", "Broadband"),
        ("City Maintenance Dept", "Maintenance"),
        ("Municipal Corp", "Property Tax")
    ]
    
    providers = {}
    for name, s_type in provider_names:
        p = db.query(Provider).filter(Provider.name == name).first()
        if not p:
            p = Provider(name=name, service_type=s_type)
            db.add(p)
            db.commit()
            db.refresh(p)
        providers[s_type] = p

    # Cleanup existing bills and payments for users 4 and 5
    db.query(Payment).filter(Payment.user_id.in_([4, 5])).delete(synchronize_session=False)
    db.query(Bill).filter(Bill.user_id.in_([4, 5])).delete(synchronize_session=False)
    db.commit()

    print("Cleared existing bills and payments for users 4 and 5.")

    # Dates
    past_due_date = now - timedelta(days=20)
    future_due_date = now + timedelta(days=15)
    paid_due_date = now - timedelta(days=30)
    paid_payment_date = now - timedelta(days=31)

    # ------------------
    # User 4 Bills
    # ------------------
    print("Seeding bills for user 4...")
    u4_bills_data = [
        # PAID
        {"provider": providers["Electricity"], "amount": 1250.50, "due": paid_due_date, "status": BillStatus.PAID, "paid": True},
        {"provider": providers["Internet"], "amount": 999.00, "due": paid_due_date, "status": BillStatus.PAID, "paid": True},
        # PENDING
        {"provider": providers["Maintenance"], "amount": 2500.00, "due": future_due_date, "status": BillStatus.PENDING, "paid": False},
        {"provider": providers["Electricity"], "amount": 1420.75, "due": future_due_date, "status": BillStatus.PENDING, "paid": False},
        # OVERDUE
        {"provider": providers["Internet"], "amount": 1050.00, "due": past_due_date, "status": BillStatus.OVERDUE, "paid": False},
        {"provider": providers["Electricity"], "amount": 1380.20, "due": past_due_date, "status": BillStatus.OVERDUE, "paid": False},
    ]

    for i, data in enumerate(u4_bills_data):
        bill = Bill(
            user_id=4,
            provider_id=data["provider"].id,
            amount=data["amount"],
            due_date=data["due"],
            status=data["status"],
            created_at=data["due"] - timedelta(days=15)
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)

        if data["paid"]:
            payment = Payment(
                bill_id=bill.id,
                user_id=4,
                amount_paid=data["amount"],
                penalty_amount=0,
                payment_method="Credit Card",
                transaction_id=f"txn_mock_{4}_{bill.id}_{i}",
                paid_at=paid_payment_date,
                status=PaymentStatus.SUCCESS
            )
            db.add(payment)
            db.commit()


    # ------------------
    # User 5 Bills
    # ------------------
    print("Seeding bills for user 5...")
    u5_bills_data = [
        # PAID
        {"provider": providers["Water"], "amount": 450.00, "due": paid_due_date, "status": BillStatus.PAID, "paid": True},
        {"provider": providers["Broadband"], "amount": 1200.00, "due": paid_due_date, "status": BillStatus.PAID, "paid": True},
        # PENDING
        {"provider": providers["Gas"], "amount": 890.50, "due": future_due_date, "status": BillStatus.PENDING, "paid": False},
        {"provider": providers["Property Tax"], "amount": 5400.00, "due": future_due_date, "status": BillStatus.PENDING, "paid": False},
        # OVERDUE
        {"provider": providers["Water"], "amount": 510.25, "due": past_due_date, "status": BillStatus.OVERDUE, "paid": False},
        {"provider": providers["Gas"], "amount": 950.00, "due": past_due_date, "status": BillStatus.OVERDUE, "paid": False},
    ]

    for i, data in enumerate(u5_bills_data):
        bill = Bill(
            user_id=5,
            provider_id=data["provider"].id,
            amount=data["amount"],
            due_date=data["due"],
            status=data["status"],
            created_at=data["due"] - timedelta(days=15)
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)

        if data["paid"]:
            payment = Payment(
                bill_id=bill.id,
                user_id=5,
                amount_paid=data["amount"],
                penalty_amount=0,
                payment_method="UPI",
                transaction_id=f"txn_mock_{5}_{bill.id}_{i}",
                paid_at=paid_payment_date,
                status=PaymentStatus.SUCCESS
            )
            db.add(payment)
            db.commit()
            
    print("Seed complete!")

if __name__ == "__main__":
    seed_demo_data()
