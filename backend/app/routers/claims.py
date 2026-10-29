import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Claim, ClaimDocument, InsurancePolicy
from app.schemas import (
    ClaimCreate, ClaimResponse, ClaimDecision, DocumentCreate, DocumentResponse
)
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/claims", tags=["Hồ sơ yêu cầu bồi thường"])

@router.get("", response_model=List[ClaimResponse])
def list_claims(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách hồ sơ yêu cầu bồi thường:
    - Customer chỉ xem các claim của mình.
    - Admin và Claims Officer xem tất cả.
    """
    query = db.query(Claim)
    if current_user.role == "customer":
        query = query.filter(Claim.customer_id == current_user.id)
    
    if status:
        query = query.filter(Claim.status == status)
    if search:
        query = query.filter(Claim.claim_number.ilike(f"%{search}%"))

    claims = query.order_by(Claim.created_at.desc()).all()
    results = []
    for c in claims:
        res = ClaimResponse.from_orm(c)
        res.customer_name = c.customer.full_name if c.customer else None
        res.product_name = c.policy.product.product_name if (c.policy and c.policy.product) else None
        res.documents = [DocumentResponse.from_orm(d) for d in c.documents]
        results.append(res)
    return results

@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim_detail(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xem chi tiết một hồ sơ bồi thường kèm danh sách chứng từ."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Hồ sơ bồi thường không tồn tại.")
    if current_user.role == "customer" and claim.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập hồ sơ này.")

    res = ClaimResponse.from_orm(claim)
    res.customer_name = claim.customer.full_name if claim.customer else None
    res.product_name = claim.policy.product.product_name if (claim.policy and claim.policy.product) else None
    res.documents = [DocumentResponse.from_orm(d) for d in claim.documents]
    return res

@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
def submit_claim(
    claim_in: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Nộp hồ sơ yêu cầu bồi thường mới:
    - Kiểm tra hợp đồng phải ở trạng thái ACTIVE
    - Số tiền yêu cầu phải lớn hơn 0
    - Lưu chứng từ/hóa đơn đính kèm
    """
    if claim_in.claimed_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Số tiền yêu cầu bồi thường phải lớn hơn 0 VNĐ."
        )

    policy = db.query(InsurancePolicy).filter(InsurancePolicy.id == claim_in.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Hợp đồng bảo hiểm không tồn tại.")

    # Business Rule BR-001: Chỉ hợp đồng ACTIVE mới được tạo claim
    if policy.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hợp đồng bảo hiểm đang ở trạng thái '{policy.status}', không đủ điều kiện yêu cầu bồi thường."
        )

    if current_user.role == "customer" and policy.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn chỉ được nộp hồ sơ bồi thường cho hợp đồng của chính mình.")

    claim_num = f"CLM-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    new_claim = Claim(
        claim_number=claim_num,
        policy_id=policy.id,
        customer_id=policy.customer_id,
        incident_date=claim_in.incident_date,
        claimed_amount=claim_in.claimed_amount,
        approved_amount=0.0,
        diagnosis=claim_in.diagnosis,
        hospital_name=claim_in.hospital_name or "Bệnh viện đa khoa",
        status="PENDING",
        fraud_risk_score=0
    )
    db.add(new_claim)
    db.commit()
    db.refresh(new_claim)

    # Thêm chứng từ đính kèm nếu có
    if claim_in.documents:
        for doc in claim_in.documents:
            c_doc = ClaimDocument(
                claim_id=new_claim.id,
                document_type=doc.document_type,
                file_path=doc.file_path,
                invoice_amount=doc.invoice_amount,
                notes=doc.notes
            )
            db.add(c_doc)
        db.commit()
        db.refresh(new_claim)

    res = ClaimResponse.from_orm(new_claim)
    res.customer_name = new_claim.customer.full_name
    res.product_name = policy.product.product_name
    res.documents = [DocumentResponse.from_orm(d) for d in new_claim.documents]
    return res

@router.post("/{claim_id}/decision", response_model=ClaimResponse)
def decide_claim(
    claim_id: int,
    decision: ClaimDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "claims_officer"]))
):
    """
    Giám định viên hoặc Admin phê duyệt hoặc từ chối bồi thường:
    - Ràng buộc: Số tiền duyệt không được vượt quá hạn mức tối đa của gói bảo hiểm (BR-004)
    - Cập nhật trạng thái sang APPROVED hoặc REJECTED
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Hồ sơ bồi thường không tồn tại.")

    max_limit = claim.policy.product.max_coverage_limit if (claim.policy and claim.policy.product) else 999999999.0
    if decision.status == "APPROVED" and decision.approved_amount > max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Số tiền phê duyệt ({decision.approved_amount:,.0f} VNĐ) không được vượt quá hạn mức bảo vệ tối đa của hợp đồng ({max_limit:,.0f} VNĐ)."
        )

    claim.approved_amount = decision.approved_amount if decision.status == "APPROVED" else 0.0
    claim.status = decision.status
    claim.officer_notes = decision.officer_notes
    claim.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(claim)

    res = ClaimResponse.from_orm(claim)
    res.customer_name = claim.customer.full_name if claim.customer else None
    res.product_name = claim.policy.product.product_name if (claim.policy and claim.policy.product) else None
    res.documents = [DocumentResponse.from_orm(d) for d in claim.documents]
    return res
