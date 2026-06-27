import os
import sys

# Add backend directory to module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.core import Bill, BillStatus, Payment

def fix_inconsistent_payments():
    db = SessionLocal()
    try:
        # Find all bills that are currently PENDING or OVERDUE
        bills = db.query(Bill).filter(Bill.status.in_([BillStatus.PENDING, BillStatus.OVERDUE])).all()
        bill_ids = [b.id for b in bills]
        
        if bill_ids:
            # Delete any Payment records for these bills so they can be paid again
            # This fixes the "Duplicate transaction. Bill is already paid" error
            deleted_count = db.query(Payment).filter(Payment.bill_id.in_(bill_ids)).delete(synchronize_session=False)
            db.commit()
            print(f"Successfully cleaned up {deleted_count} orphaned payment records for test bills.")
        else:
            print("No inconsistent bills found.")
            
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_inconsistent_payments()
