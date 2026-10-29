import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    identity_card = Column(String(50), nullable=True) # CCCD / CMND
    role = Column(String(50), default="customer", nullable=False) # admin, claims_officer, agent, customer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    policies = relationship("InsurancePolicy", back_populates="customer")
    claims = relationship("Claim", back_populates="customer")


class InsuranceProduct(Base):
    __tablename__ = "insurance_products"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(50), unique=True, index=True, nullable=False)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), default="Sức khỏe") # Sức khỏe, Tai nạn, Nhân thọ, Tài sản
    description = Column(Text, nullable=True)
    max_coverage_limit = Column(Float, nullable=False) # Hạn mức bảo vệ tối đa (VNĐ)
    base_annual_premium = Column(Float, nullable=False) # Phí bảo hiểm năm cơ bản
    terms_and_conditions = Column(Text, nullable=True) # Quy tắc điều khoản & điểm loại trừ
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    policies = relationship("InsurancePolicy", back_populates="product")


class InsurancePolicy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_number = Column(String(100), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("insurance_products.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_sum_insured = Column(Float, nullable=False) # Mệnh giá bảo vệ tối đa
    premium_amount = Column(Float, nullable=False) # Phí bảo hiểm định kỳ
    payment_cycle = Column(String(50), default="ANNUALLY") # MONTHLY, QUARTERLY, ANNUALLY
    status = Column(String(50), default="ACTIVE", index=True) # ACTIVE, PENDING, EXPIRED, CANCELLED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    customer = relationship("User", back_populates="policies")
    product = relationship("InsuranceProduct", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")
    payments = relationship("PremiumPayment", back_populates="policy")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(100), unique=True, index=True, nullable=False)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    incident_date = Column(DateTime, nullable=False)
    claimed_amount = Column(Float, nullable=False) # Số tiền khách hàng yêu cầu
    approved_amount = Column(Float, default=0.0) # Số tiền giám định viên duyệt chi trả
    diagnosis = Column(Text, nullable=False) # Chẩn đoán y khoa / Lý do tổn thất
    hospital_name = Column(String(255), default="Bệnh viện đa khoa")
    status = Column(String(50), default="PENDING", index=True) # PENDING, UNDER_REVIEW, APPROVED, REJECTED
    fraud_risk_score = Column(Integer, default=0) # Điểm nghi vấn gian lận 1-100 do AI chấm
    ai_assessment_notes = Column(Text, nullable=True) # Chi tiết đánh giá JSON/Text từ AI
    officer_notes = Column(Text, nullable=True) # Nhận xét & quyết định của Giám định viên
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    policy = relationship("InsurancePolicy", back_populates="claims")
    customer = relationship("User", back_populates="claims")
    documents = relationship("ClaimDocument", back_populates="claim", cascade="all, delete-orphan")


class ClaimDocument(Base):
    __tablename__ = "claim_documents"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    document_type = Column(String(100), nullable=False) # Hóa đơn viện phí, Giấy ra viện, Bảng kê thuốc
    file_path = Column(String(500), nullable=False)
    invoice_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    claim = relationship("Claim", back_populates="documents")


class PremiumPayment(Base):
    __tablename__ = "premium_payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_code = Column(String(100), unique=True, index=True, nullable=False)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    period_name = Column(String(100), nullable=False) # Ví dụ: Kỳ 2026-Q1, Kỳ Năm 2026
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), default="BANK_TRANSFER") # BANK_TRANSFER, MOMO, VNPAY, CASH
    payment_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="PAID") # PAID, OVERDUE, PENDING
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    policy = relationship("InsurancePolicy", back_populates="payments")


class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    feature_name = Column(String(100), nullable=False)
    prompt_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    execution_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
