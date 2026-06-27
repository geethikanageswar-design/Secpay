from sqlalchemy.orm import Session
from app.models.core import User, Provider, Bill, Payment, BillStatus, PaymentStatus
from app.schemas.schemas import UserCreate, ProviderCreate, BillCreate, PaymentCreate
from app.utils.security import get_password_hash
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
import uuid
import logging
import random
import os
import razorpay

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET else None

logger = logging.getLogger(__name__)

# User Services
def create_user(db: Session, user: UserCreate):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# Provider Services
def create_provider(db: Session, provider: ProviderCreate):
    db_provider = db.query(Provider).filter(Provider.name == provider.name).first()
    if db_provider:
        raise HTTPException(status_code=400, detail="Provider already exists")
    
    new_provider = Provider(name=provider.name, service_type=provider.service_type)
    db.add(new_provider)
    db.commit()
    db.refresh(new_provider)
    return new_provider

def get_providers(db: Session):
    return db.query(Provider).all()

def toggle_provider_status(db: Session, provider_id: int):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    provider.is_active = not provider.is_active
    db.commit()
    db.refresh(provider)
    return provider

# Bill Services
def create_bill(db: Session, bill: BillCreate):
    if bill.amount < 0:
        raise HTTPException(status_code=400, detail="Bill amount cannot be negative")

    # Verify provider exists and is active
    provider = db.query(Provider).filter(Provider.id == bill.provider_id).first()
    if not provider:
         raise HTTPException(status_code=404, detail="Provider not found")
    if not provider.is_active:
         raise HTTPException(status_code=400, detail="Cannot create bill for inactive provider")
         
    new_bill = Bill(
        user_id=bill.user_id,
        provider_id=bill.provider_id,
        amount=bill.amount,
        due_date=bill.due_date,
        status=BillStatus.PENDING
    )
    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)
    return new_bill

def update_overdue_bills(db: Session, bills):
    changed = False
    for b in bills:
        if b.status == BillStatus.PENDING and getattr(b, 'due_date', None) and b.due_date.date() < datetime.now().date():
            b.status = BillStatus.OVERDUE
            changed = True
    if changed:
        db.commit()

def get_user_bills(db: Session, user_id: int):
    bills = db.query(Bill).filter(Bill.user_id == user_id).all()
    update_overdue_bills(db, bills)
    return bills

def get_bill_by_id(db: Session, bill_id: int, user_id: int):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == user_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    update_overdue_bills(db, [bill])
    return bill

# Payment Services
def process_payment(db: Session, payment: PaymentCreate, user_id: int):
    tx_id = f"TXN-{uuid.uuid4().hex.upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(f"Payment attempt: transaction_id={tx_id} user_id={user_id} bill_id={payment.bill_id} timestamp={timestamp}")

    bill = get_bill_by_id(db, payment.bill_id, user_id)
    
    if bill.status in [BillStatus.PAID]:
        logger.warning(f"Payment failure: transaction_id={tx_id} user_id={user_id} bill_id={payment.bill_id} timestamp={timestamp} reason=Bill already PAID")
        raise HTTPException(status_code=409, detail="Bill is already paid")
        
    penalty_amount = 0.00
    if bill.status == BillStatus.OVERDUE:
        penalty_amount = round(float(bill.amount) * 0.02, 2)
        
    expected_total = round(float(bill.amount) + penalty_amount, 2)
    
    if payment.amount_paid != expected_total:
        logger.warning(f"Payment failure: transaction_id={tx_id} user_id={user_id} bill_id={payment.bill_id} timestamp={timestamp} reason=Amount mismatch")
        if penalty_amount > 0:
            raise HTTPException(status_code=400, detail=f"Payment amount must match exactly (Base: {float(bill.amount)}, Late Fee: {penalty_amount})")
        else:
            raise HTTPException(status_code=400, detail="Payment amount must match bill amount exactly")

    # Idempotency / Double payment check
    existing_payment = db.query(Payment).filter(Payment.bill_id == bill.id, Payment.status == PaymentStatus.SUCCESS).first()
    if existing_payment:
        logger.warning(f"Payment failure: transaction_id={tx_id} user_id={user_id} bill_id={payment.bill_id} timestamp={timestamp} reason=Duplicate payment")
        raise HTTPException(status_code=409, detail="Duplicate transaction. Bill is already paid")

    # Fraud detection rules:
    is_fraud = False
    if payment.amount_paid > 50000:
        is_fraud = True
        logger.warning(f"Fraud flag trigger: transaction_id={tx_id} user_id={user_id} bill_id={payment.bill_id} timestamp={timestamp} reason=High amount")
    
    two_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=2)
    failed_count = db.query(Payment).filter(
        Payment.user_id == user_id, 
        Payment.status == PaymentStatus.FAILED,
        Payment.paid_at >= two_mins_ago
    ).count()
    if failed_count >= 3:
        is_fraud = True
        logger.warning(f"Fraud flag trigger: transaction_id={tx_id} user_id={user_id} bill_id={payment.bill_id} timestamp={timestamp} reason=Too many failed attempts")

    # Masking logic
    final_method = "UNKNOWN"
    base_method = payment.payment_method.split("_")[0] if "_" in payment.payment_method else payment.payment_method
    if base_method == "CARD" and payment.card_number:
        final_method = f"{payment.payment_method}_****{payment.card_number[-4:]}"
    elif base_method == "UPI" and payment.upi_id:
        final_method = f"UPI_{payment.upi_id}"
    else:
        final_method = payment.payment_method

    # Failure Simulation
    will_fail = False
    if base_method == "CARD":
        if payment.card_number and payment.card_number.endswith("0000"):
            will_fail = True
        elif payment.card_number == "1234567890128":
            will_fail = False # Ensure test card always succeeds
        elif random.random() < 0.10:
            will_fail = True
    elif base_method == "UPI":
        if payment.upi_id and "fail" in payment.upi_id.lower():
            will_fail = True
        elif random.random() < 0.10:
            will_fail = True

    try:
        payment_status = PaymentStatus.FAILED if will_fail else PaymentStatus.SUCCESS
        
        new_payment = Payment(
            bill_id=bill.id,
            user_id=user_id,
            amount_paid=payment.amount_paid,
            penalty_amount=penalty_amount,
            payment_method=final_method,
            transaction_id=tx_id,
            status=payment_status,
            fraud_flag=is_fraud
        )
        db.add(new_payment)
        
        if payment_status == PaymentStatus.SUCCESS:
            bill.status = BillStatus.PAID
            db.add(bill)
            
        # Commit only after both Payment insert and Bill status update
        db.commit()
        db.refresh(new_payment)
        
        if payment_status == PaymentStatus.SUCCESS:
            logger.info(f"Payment success: transaction_id={tx_id} user_id={user_id} bill_id={payment.bill_id} timestamp={timestamp}")
            return new_payment, {"message": "Late fee applied for overdue bill." if penalty_amount > 0 else "Payment successful"}
        else:
            logger.info(f"Payment failure: transaction_id={tx_id} user_id={user_id} bill_id={payment.bill_id} timestamp={timestamp}")
            raise HTTPException(status_code=400, detail="Payment declined by provider")
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Payment processing transaction failed: transaction_id={tx_id} user_id={user_id} error={e}")
        raise HTTPException(status_code=500, detail="Payment processing failed")

from sqlalchemy.sql import func
from app.schemas.schemas import RazorpayOrderRequest, RazorpayVerifyRequest

def create_razorpay_order(db: Session, request: RazorpayOrderRequest, user_id: int):
    bill = get_bill_by_id(db, request.bill_id, user_id)
    
    if bill.status == BillStatus.PAID:
        raise HTTPException(status_code=409, detail="Bill is already paid")
        
    penalty_amount = 0.00
    if bill.status == BillStatus.OVERDUE:
        penalty_amount = round(float(bill.amount) * 0.02, 2)
        
    expected_total = round(float(bill.amount) + penalty_amount, 2)
    
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Razorpay is not configured on the server.")

    data = {
        "amount": int(expected_total * 100), # Razorpay uses paise
        "currency": "INR",
        "receipt": f"rcpt_{bill.id}_{user_id}_{uuid.uuid4().hex[:6]}"
    }
    
    try:
        order = razorpay_client.order.create(data=data)
        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "razorpay_key_id": RAZORPAY_KEY_ID
        }
    except Exception as e:
        logger.error(f"Failed to create Razorpay order for bill {bill.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate payment")

def verify_razorpay_payment(db: Session, request: RazorpayVerifyRequest, user_id: int):
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Razorpay is not configured on the server.")

    bill = get_bill_by_id(db, request.bill_id, user_id)
    if bill.status == BillStatus.PAID:
        raise HTTPException(status_code=409, detail="Bill is already paid")

    is_verified = False
    payment_status = PaymentStatus.PENDING

    if not request.razorpay_signature:
        payment_status = PaymentStatus.FAILED
    else:
        try:
            params_dict = {
                'razorpay_order_id': request.razorpay_order_id,
                'razorpay_payment_id': request.razorpay_payment_id,
                'razorpay_signature': request.razorpay_signature
            }
            razorpay_client.utility.verify_payment_signature(params_dict)
            is_verified = True
            payment_status = PaymentStatus.SUCCESS
        except razorpay.errors.SignatureVerificationError as e:
            logger.warning(f"Signature verification failed for {request.razorpay_payment_id}: {e}")
            payment_status = PaymentStatus.FAILED
        except Exception as e:
            logger.error(f"Error validating razorpay payment: {e}")
            raise HTTPException(status_code=500, detail="Payment verification error")

    if payment_status == PaymentStatus.SUCCESS:
        tx_id = request.razorpay_payment_id
    else:
        # Always deduplicate failures at the order level
        tx_id = f"RFAIL-{request.razorpay_order_id}"

    # Check for duplicate
    existing_payment = db.query(Payment).filter(Payment.transaction_id == tx_id).first()
    if existing_payment:
        if existing_payment.status == PaymentStatus.FAILED and payment_status == PaymentStatus.FAILED:
            raise HTTPException(status_code=400, detail="Payment failed. Duplicate attempt recorded previously.")
        elif existing_payment.status == PaymentStatus.SUCCESS:
            return existing_payment, {"message": "Payment already successful"}

    penalty_amount = 0.00
    if bill.status == BillStatus.OVERDUE:
        penalty_amount = round(float(bill.amount) * 0.02, 2)
    total_amount = round(float(bill.amount) + penalty_amount, 2)

    try:
        new_payment = Payment(
            bill_id=bill.id,
            user_id=user_id,
            amount_paid=total_amount,
            penalty_amount=penalty_amount,
            payment_method="RAZORPAY",
            transaction_id=tx_id,
            status=payment_status,
            fraud_flag=False
        )
        db.add(new_payment)

        if payment_status == PaymentStatus.SUCCESS:
            bill.status = BillStatus.PAID
            db.add(bill)
            
        db.commit()
        db.refresh(new_payment)
        
        if payment_status == PaymentStatus.SUCCESS:
            return new_payment, {"message": "Payment successful"}
        else:
            raise HTTPException(status_code=400, detail="Razorpay payment failed or signature missing.")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving payment {tx_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save payment record")

def get_transaction_stats(db: Session):
    revenue = db.query(func.sum(Payment.amount_paid)).filter(Payment.status == PaymentStatus.SUCCESS).scalar() or 0.0
    failed = db.query(Payment).filter(Payment.status == PaymentStatus.FAILED).count()
    
    transactions = db.query(Payment).order_by(Payment.paid_at.desc()).all()
    
    return {
        "total_revenue": float(revenue),
        "failed_payments_count": failed,
        "transactions": transactions
    }

def get_fraud_alerts(db: Session):
    return db.query(Payment).filter(Payment.fraud_flag == True).order_by(Payment.paid_at.desc()).all()
