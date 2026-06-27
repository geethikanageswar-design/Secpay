import os
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

# Add the app directory to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.core import User, Provider, Bill, Payment, BillStatus, PaymentStatus, UserRole
from app.database import SessionLocal
from app.utils.security import get_password_hash

def seed_custom_data():
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    # 1. Ensure Dolly is ADMIN
    dolly = db.query(User).filter(User.email == "dolly@gmail.com").first()
    if dolly:
        dolly.role = UserRole.ADMIN
        db.commit()
    else:
        dolly = User(
            name="Dolly",
            email="dolly@gmail.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.ADMIN
        )
        db.add(dolly)
        db.commit()
        db.refresh(dolly)

    # 2. Create 2 more users with user-level access
    users_data = [
        {"name": "John Doe", "email": "john@example.com", "password": "password123"},
        {"name": "Jane Smith", "email": "jane@example.com", "password": "password123"}
    ]

    users = {}
    users["dolly@gmail.com"] = dolly

    for u_data in users_data:
        user = db.query(User).filter(User.email == u_data["email"]).first()
        if not user:
            print(f"Creating user {u_data['name']}")
            user = User(
                name=u_data["name"],
                email=u_data["email"],
                password_hash=get_password_hash(u_data["password"]),
                role=UserRole.USER
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update password hash just in case
            user.password_hash = get_password_hash(u_data["password"])
            user.role = UserRole.USER
            db.commit()
        users[u_data["email"]] = user

    # Get providers
    providers = {p.service_type: p for p in db.query(Provider).all()}

    # 3. Clean up existing bills and payments for these users
    user_ids = [u.id for u in users.values()]
    db.query(Payment).filter(Payment.user_id.in_(user_ids)).delete(synchronize_session=False)
    db.query(Bill).filter(Bill.user_id.in_(user_ids)).delete(synchronize_session=False)
    db.commit()
    print("Cleared existing bills and payments for John, Jane, and Dolly.")

    # 4. Generate custom bills and payments
    
    # --- Dolly (ADMIN) ---
    print("Seeding bills for Dolly...")
    dolly_bills = [
        # Paid Bill
        {"provider": providers["Electricity"], "amount": 1500.00, "due": now - timedelta(days=5), "status": BillStatus.PAID, "paid": True},
        # Pending Bill
        {"provider": providers["Water"], "amount": 350.00, "due": now + timedelta(days=10), "status": BillStatus.PENDING, "paid": False}
    ]
    seed_user_bills(db, users["dolly@gmail.com"].id, dolly_bills)

    # --- John Doe (USER) ---
    print("Seeding bills for John Doe...")
    john_bills = [
        # Paid Bill
        {"provider": providers["Internet"], "amount": 999.00, "due": now - timedelta(days=12), "status": BillStatus.PAID, "paid": True},
        # Pending Bill
        {"provider": providers["Electricity"], "amount": 1850.50, "due": now + timedelta(days=15), "status": BillStatus.PENDING, "paid": False},
        # Overdue Bill
        {"provider": providers["Gas"], "amount": 650.00, "due": now - timedelta(days=5), "status": BillStatus.OVERDUE, "paid": False}
    ]
    seed_user_bills(db, users["john@example.com"].id, john_bills)

    # --- Jane Smith (USER) ---
    print("Seeding bills for Jane Smith...")
    jane_bills = [
        # Paid Bill
        {"provider": providers["Broadband"], "amount": 1200.00, "due": now - timedelta(days=20), "status": BillStatus.PAID, "paid": True},
        # Pending Bill
        {"provider": providers["Property Tax"], "amount": 4500.00, "due": now + timedelta(days=25), "status": BillStatus.PENDING, "paid": False},
        # Overdue Bill
        {"provider": providers["Water"], "amount": 420.00, "due": now - timedelta(days=8), "status": BillStatus.OVERDUE, "paid": False}
    ]
    seed_user_bills(db, users["jane@example.com"].id, jane_bills)

    # Add a failed payment attempt for Jane to make dashboard history look realistic
    overdue_bill = db.query(Bill).filter(Bill.user_id == users["jane@example.com"].id, Bill.status == BillStatus.OVERDUE).first()
    if overdue_bill:
        failed_payment = Payment(
            bill_id=overdue_bill.id,
            user_id=users["jane@example.com"].id,
            amount_paid=428.40, # including late fee 2%
            penalty_amount=8.40,
            payment_method="CARD_VISA_****1111",
            transaction_id="TXN-FAILED-DEMO-JANE",
            status=PaymentStatus.FAILED,
            paid_at=now - timedelta(days=1)
        )
        db.add(failed_payment)
        db.commit()

    print("Custom seeding complete!")
    db.close()

def seed_user_bills(db: Session, user_id: int, bills_data):
    for i, data in enumerate(bills_data):
        bill = Bill(
            user_id=user_id,
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
                user_id=user_id,
                amount_paid=data["amount"],
                penalty_amount=0.00,
                payment_method="CARD_VISA_****4321" if i % 2 == 0 else "UPI_demo@upi",
                transaction_id=f"TXN-SUCCESS-{user_id}-{bill.id}",
                paid_at=data["due"] - timedelta(days=1),
                status=PaymentStatus.SUCCESS
            )
            db.add(payment)
            db.commit()

if __name__ == "__main__":
    seed_custom_data()
