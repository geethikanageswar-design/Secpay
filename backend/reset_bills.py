import os
import sys

# Add backend directory to module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.core import Bill, BillStatus

def revert_bills():
    db = SessionLocal()
    try:
        # Find 5 recently PAID bills and set them to PENDING
        bills = db.query(Bill).filter(Bill.status == BillStatus.PAID).limit(5).all()
        
        count = 0
        for bill in bills:
            bill.status = BillStatus.PENDING
            count += 1
            
        db.commit()
        print(f"Successfully reverted {count} bills from PAID to PENDING status.")
    except Exception as e:
        db.rollback()
        print(f"Failed to revert bills: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    revert_bills()
