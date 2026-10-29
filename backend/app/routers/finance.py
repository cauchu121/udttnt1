import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, PremiumPayment, InsurancePolicy
from app.schemas import PaymentCreate, PaymentResponse
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/finance", tags=["Quản lý Thu phí Định kỳ"])

@router.get("/payments", response_model=List[PaymentResponse])
def list_payments(
    policy_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách các giao dịch đóng phí bảo hiểm."""
    query = db.query(PremiumPayment)
    if policy_id:
        query = query.filter(PremiumPayment.policy_id == policy_id)
    if current_user.role == "customer":
        user_policy_ids = [p.id for p in current_user.policies]
        if not user_policy_ids:
            return []
        query = query.filter(PremiumPayment.policy_id.in_(user_policy_ids))
    payments = query.order_by(PremiumPayment.created_at.desc()).all()
    results = []
    for pay in payments:
        res = PaymentResponse.from_orm(pay)
        res.policy_number = pay.policy.policy_number if pay.policy else f"POL-{pay.policy_id:04d}"
        res.customer_name = pay.policy.customer.full_name if (pay.policy and pay.policy.customer) else None
        results.append(res)
    return results

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def make_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ghi nhận thanh toán phí bảo hiểm định kỳ và gia hạn hiệu lực hợp đồng."""
    policy = db.query(InsurancePolicy).filter(InsurancePolicy.id == payment_in.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Hợp đồng bảo hiểm không tồn tại.")

    code = f"PAY-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    new_payment = PremiumPayment(
        payment_code=code,
        policy_id=policy.id,
        period_name=payment_in.period_name,
        amount=payment_in.amount,
        payment_method=payment_in.payment_method,
        payment_date=datetime.datetime.utcnow(),
        status="PAID",
        receipt_image=payment_in.receipt_image
    )
    db.add(new_payment)

    # Nếu hợp đồng đang chờ kích hoạt hoặc hết hạn, nộp phí xong chuyển sang ACTIVE
    if policy.status in ["PENDING", "EXPIRED"]:
        policy.status = "ACTIVE"

    db.commit()
    db.refresh(new_payment)

    res = PaymentResponse.from_orm(new_payment)
    res.policy_number = policy.policy_number
    res.customer_name = policy.customer.full_name if policy.customer else None
    return res
