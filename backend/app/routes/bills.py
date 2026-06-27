from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.schemas import BillCreate, BillResponse
from app.services.crud import create_bill, get_user_bills, get_bill_by_id
from app.utils.dependencies import get_current_user, require_admin_user
from app.models.core import User
from fastapi import HTTPException

router = APIRouter(
    prefix="/api/bills",
    tags=["Bills"]
)

@router.post("/")
def create_new_bill(bill: BillCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin_user)):
    return {
        "status": "success",
        "data": create_bill(db=db, bill=bill)
    }

@router.get("/user/{user_id}")
def get_user_bills_route(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized to view these bills")
    return {
        "status": "success", 
        "data": get_user_bills(db=db, user_id=user_id)
    }

@router.get("/{bill_id}")
def get_bill_route(bill_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {
        "status": "success",
        "data": get_bill_by_id(db=db, bill_id=bill_id, user_id=current_user.id)
    }
