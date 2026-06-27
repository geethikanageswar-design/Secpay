from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database import Base

class BillStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"

class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"

class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    bills = relationship("Bill", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    service_type = Column(String(50), nullable=False) # e.g., "Electricity", "Water"
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    bills = relationship("Bill", back_populates="provider")


class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(Enum(BillStatus), default=BillStatus.PENDING, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="bills")
    provider = relationship("Provider", back_populates="bills")
    payments = relationship("Payment", back_populates="bill")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount_paid = Column(Numeric(10, 2), nullable=False)
    penalty_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    payment_method = Column(String(50))
    transaction_id = Column(String(100), unique=True, index=True)
    paid_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    fraud_flag = Column(Boolean, default=False, index=True)

    bill = relationship("Bill", back_populates="payments")
    user = relationship("User", back_populates="payments")
