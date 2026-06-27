import os
import sys

# Add backend directory to module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.core import Bill, BillStatus, Payment

def force_reset_all():
    db = SessionLocal()
    try:
        # Delete all payments to clear history completely
        deleted_payments = db.query(Payment).delete(synchronize_session=False)
        
        # Set all bills to PENDING
        db.query(Bill).update({"status": BillStatus.PENDING}, synchronize_session=False)
        
        db.commit()
        print(f"Force reset complete. Deleted {deleted_payments} payments and set all bills to PENDING.")
    except Exception as e:
        db.rollback()
        print(f"Error during force reset: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    force_reset_all()
