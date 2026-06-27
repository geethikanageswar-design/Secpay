import os
import sys

# Add backend directory to module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.core import Bill, BillStatus, Payment, PaymentStatus
from app.services.crud import verify_razorpay_payment, create_razorpay_order
from app.schemas.schemas import RazorpayOrderRequest, RazorpayVerifyRequest
from fastapi import HTTPException
import traceback

def test():
    db = SessionLocal()
    try:
        bill = db.query(Bill).filter(Bill.status == BillStatus.PENDING).first()
        if not bill:
            print("No pending bill found")
            return
            
        print(f"Testing with bill id: {bill.id}, user_id: {bill.user_id}")
        
        # Create an order first
        req = RazorpayOrderRequest(bill_id=bill.id)
        res = create_razorpay_order(db, req, bill.user_id)
        order_id = getattr(res, "order_id", res.get("order_id", None) if isinstance(res, dict) else None)
        print(f"Created order: {order_id}")
        
        # Test 1: Verifying a failure (missing signature)
        print("\n--- Test 1: Missing Signature ---")
        verify_req1 = RazorpayVerifyRequest(
            razorpay_order_id=order_id,
            razorpay_payment_id="",
            razorpay_signature="",
            bill_id=bill.id
        )
        try:
            # We expect a 400 exception, but it should still log a failure
            verify_razorpay_payment(db, verify_req1, bill.user_id)
        except HTTPException as e:
            print(f"Caught expected HTTP Exception: {e.detail}")
        
        # Check DB for failure record
        payments = db.query(Payment).filter(Payment.transaction_id == f"RFAIL-{order_id}").all()
        print(f"Found {len(payments)} failure payment records for this order ID.")
        
        # Test 2: Verifying DUPLICATE failure
        print("\n--- Test 2: Duplicate Failure ---")
        try:
            # Send SAME verification request
            verify_razorpay_payment(db, verify_req1, bill.user_id)
        except HTTPException as e:
            print(f"Caught expected duplicate HTTP Exception: {e.detail}")
            
        payments_after = db.query(Payment).filter(Payment.transaction_id == f"RFAIL-{order_id}").all()
        print(f"Found {len(payments_after)} failure payment records for this order ID (should still be 1).")
        
        # Test 3: Verifying SUCCESS on same bill (mocking verify_payment_signature)
        print("\n--- Test 3: SUCCESS Payment Workflow ---")
        import razorpay
        # Mocking razorpay verification just for the test
        from app.services import crud
        class MockUtility:
            def verify_payment_signature(self, params):
                return True
        crud.razorpay_client.utility = MockUtility()
        
        verify_req_success = RazorpayVerifyRequest(
            razorpay_order_id=order_id,
            razorpay_payment_id="pay_MockSuccess123",
            razorpay_signature="mock_signature",
            bill_id=bill.id
        )
        
        success_payment, msg = verify_razorpay_payment(db, verify_req_success, bill.user_id)
        print(f"Success payment result: {msg}, status: {success_payment.status}")
        
        bill_after = db.query(Bill).filter(Bill.id == bill.id).first()
        print(f"Bill status after success: {bill_after.status}")
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
