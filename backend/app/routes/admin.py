from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.dependencies import require_admin_user
from app.services import crud
from app.models.core import User

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/transactions")
def get_transactions(
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_admin_user)
):
    """
    Fetch comprehensive transaction statistics and history. ADMIN only.
    Returns standardized format: {"status": "success", "data": {...}}
    """
    stats = crud.get_transaction_stats(db)
    return {
        "status": "success",
        "data": stats
    }

@router.get("/fraud-alerts")
def get_fraud_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    """
    Fetch all payments flagged as fraud. ADMIN only.
    Returns standardized format: {"status": "success", "data": {...}}
    """
    alerts = crud.get_fraud_alerts(db)
    return {
        "status": "success",
        "data": {
            "alerts": alerts
        }
    }
