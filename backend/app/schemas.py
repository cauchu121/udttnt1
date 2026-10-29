import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# --- AUTH & USER SCHEMAS ---
class UserBase(BaseModel):
    email: str
    full_name: str
    phone: Optional[str] = None
    identity_card: Optional[str] = None
    role: str = "customer"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class LoginRequest(BaseModel):
    email: str
    password: str

# --- PRODUCT SCHEMAS ---
class ProductBase(BaseModel):
    product_code: str
    product_name: str
    category: str = "Sức khỏe"
    description: Optional[str] = None
    max_coverage_limit: float
    base_annual_premium: float
    terms_and_conditions: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- POLICY SCHEMAS ---
class PolicyBase(BaseModel):
    policy_number: str
    customer_id: int
    product_id: int
    start_date: datetime.datetime
    end_date: datetime.datetime
    total_sum_insured: float
    premium_amount: float
    payment_cycle: str = "ANNUALLY"
    status: str = "ACTIVE"

class PolicyCreate(BaseModel):
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_identity: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    product_id: int
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None
    total_sum_insured: Optional[float] = None
    premium_amount: Optional[float] = None
    payment_cycle: str = "ANNUALLY"

class PolicyResponse(PolicyBase):
    id: int
    created_at: datetime.datetime
    customer_name: Optional[str] = None
    product_name: Optional[str] = None

    class Config:
        from_attributes = True

# --- CLAIM & DOCUMENT SCHEMAS ---
class DocumentCreate(BaseModel):
    document_type: str
    file_path: str
    invoice_amount: float = 0.0
    notes: Optional[str] = None

class DocumentResponse(DocumentCreate):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ClaimCreate(BaseModel):
    policy_id: int
    incident_date: datetime.datetime
    claimed_amount: float
    diagnosis: str
    hospital_name: Optional[str] = "Bệnh viện đa khoa"
    documents: Optional[List[DocumentCreate]] = []

class ClaimDecision(BaseModel):
    approved_amount: float
    status: str # APPROVED or REJECTED
    officer_notes: Optional[str] = None

class ClaimResponse(BaseModel):
    id: int
    claim_number: str
    policy_id: int
    customer_id: int
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    incident_date: datetime.datetime
    claimed_amount: float
    approved_amount: float
    diagnosis: str
    hospital_name: str
    status: str
    fraud_risk_score: int
    ai_assessment_notes: Optional[str] = None
    officer_notes: Optional[str] = None
    created_at: datetime.datetime
    documents: List[DocumentResponse] = []

    class Config:
        from_attributes = True

# --- FINANCE SCHEMAS ---
class PaymentCreate(BaseModel):
    policy_id: int
    period_name: str
    amount: float
    payment_method: str = "BANK_TRANSFER"
    receipt_image: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    payment_code: str
    policy_id: int
    policy_number: Optional[str] = None
    customer_name: Optional[str] = None
    period_name: str
    amount: float
    payment_method: str
    payment_date: datetime.datetime
    status: str
    receipt_image: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- AI COPILOT STRICT OUTPUT SCHEMAS ---
class CostItem(BaseModel):
    item_name: str
    amount: float
    reason: str = ""

class RejectedCostItem(BaseModel):
    item_name: str
    amount: float
    rejection_reason: str

class ClaimAssessmentStrictOutput(BaseModel):
    is_valid: bool
    recommended_amount: float
    max_coverage_limit: float
    fraud_risk_score: int = Field(ge=1, le=100)
    risk_level: str
    approved_items: List[CostItem] = []
    rejected_items: List[RejectedCostItem] = []
    fraud_warning_signals: List[str] = []
    assessment_conclusion: str
    disclaimer: str = (
        "Kết quả thẩm định do AI sinh ra chỉ mang tính chất tham khảo. "
        "Quyết định chi trả cuối cùng thuộc về Giám định viên con người."
    )

class ClaimAssessmentRequest(BaseModel):
    claim_id: int

class AdvisorChatRequest(BaseModel):
    message: str
    policy_id: Optional[int] = None

class AdvisorChatResponse(BaseModel):
    reply: str
    disclaimer: str = "Trợ lý AI chỉ giải đáp căn cứ trên bảng điều khoản hiện hành của hệ thống."
    suggested_questions: List[str] = []

class RiskScoringRequest(BaseModel):
    age_group: str = "30-40"
    claim_ratio: float = 0.0
    job_category: str = "Văn phòng"
    risk_notes: Optional[str] = "Sức khỏe bình thường"

class RiskScoringResponse(BaseModel):
    risk_score: int
    risk_level: str
    premium_adjustment_percent: float
    underwriting_notes: str
    recommendation: str

# --- ANALYTICS SCHEMAS ---
class DashboardAnalytics(BaseModel):
    total_active_policies: int
    total_premiums_written: float
    total_claims_paid: float
    total_claims_count: int
    pending_claims_count: int
    loss_ratio_percent: float
    monthly_trend: List[dict] = []
    category_distribution: List[dict] = []
