from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.core import Bill, BillStatus, User, Payment, PaymentStatus
from app.schemas.schemas import DashboardResponse
from app.utils.dependencies import get_current_user, require_admin_user
from sqlalchemy import func

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)

@router.get("/{user_id}")
def get_dashboard_metrics(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized to view this dashboard")

    # Fetch bills
    # Actually need to make sure we update overdue bills first! 
    # Let's import update_overdue_bills from crud
    from app.services.crud import update_overdue_bills
    bills = db.query(Bill).filter(Bill.user_id == user_id).all()
    update_overdue_bills(db, bills)
    
    # Calculate metrics
    pending_bills = [b for b in bills if b.status == BillStatus.PENDING]
    overdue_bills = [b for b in bills if b.status == BillStatus.OVERDUE]
    
    total_outstanding = sum([b.amount for b in pending_bills]) + sum([b.amount for b in overdue_bills])
    pending_count = len(pending_bills)
    overdue_count = len(overdue_bills)
    
    # Payment metrics
    paid_count = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == PaymentStatus.SUCCESS).count()
    failed_count = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == PaymentStatus.FAILED).count()
    
    dash_data = dict(
        total_outstanding=float(total_outstanding),
        pending_count=pending_count,
        overdue_count=overdue_count,
        paid_count=paid_count,
        failed_count=failed_count
    )
    return {
        "status": "success",
        "data": dash_data
    }
