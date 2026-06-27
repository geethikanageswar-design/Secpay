import os
import sys
from datetime import datetime, timedelta, timezone
import uuid

# Add the parent directory to sys.path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.core import Bill, Payment, BillStatus, PaymentStatus

def fix_consistency():
    db: Session = SessionLocal()
    try:
        # Find all bills marked as PAID
        paid_bills = db.query(Bill).filter(Bill.status == BillStatus.PAID).all()
        
        fixed_count = 0
        updated_count = 0
        
        for bill in paid_bills:
            # Check if there's a successful payment
            payment = db.query(Payment).filter(
                Payment.bill_id == bill.id, 
                Payment.status == PaymentStatus.SUCCESS
            ).first()
            
            # calculate realistic past time
            if getattr(bill, 'due_date', None):
                base_time = bill.due_date
            else:
                base_time = datetime.now()
            
            # Ensure the time is timezone aware to match UTC constraints
            if base_time.tzinfo is None:
                base_time = base_time.replace(tzinfo=timezone.utc)
                
            realistic_paid_at = base_time - timedelta(days=2)
            
            if not payment:
                tx_id = f"TXN-{uuid.uuid4().hex.upper()}"
                
                # Determine penalty if due_date was in past compared to paid_at
                # But if it's paid before due date, penalty is 0
                penalty = 0.00
                
                new_payment = Payment(
                    bill_id=bill.id,
                    user_id=bill.user_id,
                    amount_paid=bill.amount,
                    penalty_amount=penalty,
                    payment_method="CARD_****1234",
                    transaction_id=tx_id,
                    status=PaymentStatus.SUCCESS,
                    fraud_flag=False,
                    paid_at=realistic_paid_at
                )
                db.add(new_payment)
                fixed_count += 1
            else:
                # Update existing payment to have realistic past timestamp if it just defaults to now
                # In standard scenarios, paid_at would be around when the script ran. Let's fix it anyway to be in the past to satisfy the demo requirements.
                payment.paid_at = realistic_paid_at
                db.add(payment)
                updated_count += 1
                
        db.commit()
        print(f"Fixed {fixed_count} bills by creating missing Payment records.")
        print(f"Updated {updated_count} existing Payment records with realistic past timestamps.")
        
    except Exception as e:
        print(f"Error fixing data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_consistency()
