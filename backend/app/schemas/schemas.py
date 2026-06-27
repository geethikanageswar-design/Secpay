from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime
from typing import Optional
import re
from app.models.core import BillStatus, PaymentStatus, UserRole

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# User Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True

# Provider Schemas
class ProviderCreate(BaseModel):
    name: str
    service_type: str

class ProviderResponse(BaseModel):
    id: int
    name: str
    service_type: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Bill Schemas
class BillCreate(BaseModel):
    user_id: int
    provider_id: int
    amount: float
    due_date: datetime

class BillResponse(BaseModel):
    id: int
    user_id: int
    provider_id: int
    amount: float
    due_date: datetime
    status: BillStatus
    created_at: datetime

    class Config:
        from_attributes = True

# Payment Schemas
class PaymentCreate(BaseModel):
    bill_id: int
    amount_paid: float
    payment_method: str # e.g. CARD_VISA, UPI, NETBANKING_HDFC, WALLET_PAYTM

    # Card fields - Using Field(exclude=True) to ensure they are never returned back from this schema if reflected
    cardholder_name: Optional[str] = Field(default=None, exclude=True)
    card_number: Optional[str] = Field(default=None, exclude=True)
    expiry_date: Optional[str] = Field(default=None, exclude=True)
    cvv: Optional[str] = Field(default=None, exclude=True)

    # UPI fields
    upi_id: Optional[str] = None

    # Bank/Wallet
    bank_name: Optional[str] = None
    wallet_provider: Optional[str] = None

    @validator("payment_method")
    def validate_payment_method(cls, v):
        methods = ["CARD", "UPI"]
        base_method = v.split("_")[0] if "_" in v else v
        if base_method not in methods:
            raise ValueError(f"Invalid payment method. Must be one of {methods}")
        return v

    @validator("cardholder_name")
    def validate_cardholder_name(cls, v, values):
        if values.get("payment_method", "").startswith("CARD"):
            if not v or len(v.strip()) < 3:
                raise ValueError("Cardholder name must be at least 3 characters long.")
        return v
    @validator("card_number")
    def validate_card_number(cls, v, values):
        method = values.get("payment_method", "")
        if method.startswith("CARD"):
            if not v or not v.isdigit():
                raise ValueError("Invalid card number. Must be numeric.")
            if not (13 <= len(v) <= 16):
                raise ValueError("Invalid card number length. Must be between 13 and 16 digits.")
            # Basic Luhn check
            digits = [int(x) for x in v]
            odd_digits = digits[-1::-2]
            even_digits = [sum(divmod(2 * d, 10)) for d in digits[-2::-2]]
            if (sum(odd_digits) + sum(even_digits)) % 10 != 0:
                raise ValueError("Invalid card number (Luhn check failed).")
        return v

    @validator("expiry_date")
    def validate_expiry_date(cls, v, values):
        if values.get("payment_method", "").startswith("CARD"):
            if not v or not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", v):
                raise ValueError("Invalid expiry date format. Must be MM/YY.")
            month, year = map(int, v.split('/'))
            now = datetime.now()
            current_year, current_month = now.year % 100, now.month
            if year < current_year or (year == current_year and month < current_month):
                raise ValueError("Card is expired.")
        return v

    @validator("cvv")
    def validate_cvv(cls, v, values):
        if values.get("payment_method", "").startswith("CARD"):
            if not v or not v.isdigit() or not (3 <= len(v) <= 4):
                raise ValueError("Invalid CVV. Must be 3 or 4 digits.")
        return v

    @validator("upi_id")
    def validate_upi_id(cls, v, values):
        if values.get("payment_method") == "UPI":
            if not v or not re.match(r"^[a-zA-Z0-9.\-_]+@[a-zA-Z]+$", v):
                raise ValueError("Invalid UPI ID format. Must be username@provider.")
        return v

class PaymentResponse(BaseModel):
    id: int
    bill_id: int
    user_id: int
    amount_paid: float
    penalty_amount: float
    payment_method: Optional[str]
    transaction_id: Optional[str]
    paid_at: datetime
    status: PaymentStatus

    class Config:
        from_attributes = True

class TransactionDashboardResponse(BaseModel):
    total_revenue: float
    failed_payments_count: int
    transactions: list[PaymentResponse]

class FraudAlertResponse(BaseModel):
    alerts: list[PaymentResponse]

# Dashboard Schemas
class DashboardResponse(BaseModel):
    total_outstanding: float
    pending_count: int
    overdue_count: int
    paid_count: int
    failed_count: int

# Razorpay Schemas
class RazorpayOrderRequest(BaseModel):
    bill_id: int

class RazorpayOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    razorpay_key_id: str

class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    bill_id: int
