import os
import sys

# Add backend directory to module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.core import Bill, BillStatus, Payment
from app.services.crud import create_razorpay_order
from app.schemas.schemas import RazorpayOrderRequest
import traceback

def test():
    db = SessionLocal()
    try:
        bill = db.query(Bill).filter(Bill.status == BillStatus.PENDING).first()
        if not bill:
            print("No pending bill found")
            return
            
        print(f"Testing with bill id: {bill.id}, user_id: {bill.user_id}")
        req = RazorpayOrderRequest(bill_id=bill.id)
        
        try:
            res = create_razorpay_order(db, req, bill.user_id)
            print("Success!")
            print(res)
        except Exception as e:
            print(f"Exception caught:")
            traceback.print_exc()
            
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test()
