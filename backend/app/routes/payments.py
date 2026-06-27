from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.schemas.schemas import PaymentCreate, RazorpayOrderRequest, RazorpayVerifyRequest
from app.services.crud import process_payment, create_razorpay_order, verify_razorpay_payment
from app.utils.dependencies import get_current_user, require_admin_user
from app.models.core import User, Payment, Provider, Bill

router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"]
)

@router.post("/")
def make_payment(request: Request, payment: PaymentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    payment_record, result_msg = process_payment(db=db, payment=payment, user_id=current_user.id)
    return {
        "status": "success",
        "message": result_msg.get("message", "Payment successful"),
        "data": payment_record
    }

@router.post("/create-order")
def create_order(request: Request, order_request: RazorpayOrderRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_razorpay_order(db=db, request=order_request, user_id=current_user.id)

@router.post("/verify")
def verify_payment(request: Request, verify_request: RazorpayVerifyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    payment_record, result_msg = verify_razorpay_payment(db=db, request=verify_request, user_id=current_user.id)
    return {
        "status": "success",
        "message": result_msg.get("message", "Payment verified and successful"),
        "data": payment_record
    }

@router.get("/history")
def get_payment_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Build a custom joined response to return all necessary data for the frontend table
    history = db.query(Payment, Bill, Provider).join(
        Bill, Payment.bill_id == Bill.id
    ).join(
        Provider, Bill.provider_id == Provider.id
    ).filter(
        Payment.user_id == current_user.id
    ).order_by(
        desc(Payment.paid_at)
    ).all()
    
    formatted_history = []
    for p, b, prov in history:
        formatted_history.append({
            "transaction_id": p.transaction_id,
            "bill_name": f"{prov.service_type} Bill",
            "provider_name": prov.name,
            "amount": float(p.amount_paid),
            "payment_method": p.payment_method,
            "status": p.status.value,
            "payment_date": p.paid_at,
            "sender_name": current_user.name,
            "receiver_name": prov.name,
            "penalty_amount": float(p.penalty_amount)
        })
        
    return {
        "status": "success",
        "data": formatted_history
    }
