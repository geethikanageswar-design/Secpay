from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import ProviderCreate, ProviderResponse
from app.services.crud import create_provider, get_providers, toggle_provider_status
from app.utils.dependencies import require_admin_user, get_current_user
from app.models.core import User
from typing import List

router = APIRouter(
    prefix="/api/providers",
    tags=["Providers"]
)

@router.post("/")
def create_new_provider(provider: ProviderCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin_user)):
    return {
        "status": "success",
        "data": create_provider(db=db, provider=provider)
    }

@router.get("/")
def read_providers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {
        "status": "success",
        "data": get_providers(db=db)
    }

@router.patch("/{id}/toggle")
def toggle_provider(id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin_user)):
    return {
        "status": "success",
        "data": toggle_provider_status(db=db, provider_id=id)
    }
