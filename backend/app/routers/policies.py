import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, InsuranceProduct, InsurancePolicy, PremiumPayment
from app.schemas import (
    ProductCreate, ProductResponse, PolicyCreate, PolicyResponse
)
from app.auth import get_current_user, require_roles, hash_password

router = APIRouter(prefix="/policies", tags=["Gói bảo hiểm & Hợp đồng"])

# --- PRODUCTS (GÓI BẢO HIỂM) ---

@router.get("/products", response_model=List[ProductResponse])
def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lấy danh sách các gói sản phẩm bảo hiểm có hỗ trợ tìm kiếm và lọc."""
    query = db.query(InsuranceProduct).filter(InsuranceProduct.is_active == True)
    if category:
        query = query.filter(InsuranceProduct.category == category)
    if search:
        query = query.filter(InsuranceProduct.product_name.ilike(f"%{search}%"))
    return query.all()

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """Admin tạo mới một gói sản phẩm bảo hiểm."""
    existing = db.query(InsuranceProduct).filter(InsuranceProduct.product_code == product_in.product_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mã gói sản phẩm bảo hiểm đã tồn tại.")

    product = InsuranceProduct(**product_in.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """Admin cập nhật thông tin sản phẩm bảo hiểm."""
    product = db.query(InsuranceProduct).filter(InsuranceProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy gói sản phẩm bảo hiểm.")
    
    for key, value in product_in.dict().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product

# --- POLICIES (HỢP ĐỒNG BẢO HIỂM) ---

@router.get("", response_model=List[PolicyResponse])
def list_policies(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách hợp đồng bảo hiểm:
    - Customer chỉ xem hợp đồng của chính mình.
    - Admin, Claims Officer, Agent được xem toàn bộ.
    """
    query = db.query(InsurancePolicy)
    if current_user.role == "customer":
        query = query.filter(InsurancePolicy.customer_id == current_user.id)
    
    if status:
        query = query.filter(InsurancePolicy.status == status)
    if search:
        query = query.filter(InsurancePolicy.policy_number.ilike(f"%{search}%"))

    policies = query.all()
    results = []
    for p in policies:
        res = PolicyResponse.from_orm(p)
        res.customer_name = p.customer.full_name if p.customer else None
        res.product_name = p.product.product_name if p.product else None
        results.append(res)
    return results

@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy_detail(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xem chi tiết một hợp đồng bảo hiểm."""
    policy = db.query(InsurancePolicy).filter(InsurancePolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Hợp đồng bảo hiểm không tồn tại.")
    if current_user.role == "customer" and policy.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập hợp đồng này.")

    res = PolicyResponse.from_orm(policy)
    res.customer_name = policy.customer.full_name if policy.customer else None
    res.product_name = policy.product.product_name if policy.product else None
    return res

@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def issue_policy(
    policy_in: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Phát hành hợp đồng bảo hiểm mới:
    - Customer có thể tự mua cho mình.
    - Admin/Agent có thể phát hành cho khách hàng có sẵn HOẶC nhập thông tin tự do cho khách hàng mới.
    """
    customer = None
    if current_user.role == "customer":
        customer = current_user
    elif policy_in.customer_id and policy_in.customer_id > 0:
        customer = db.query(User).filter(User.id == policy_in.customer_id).first()
    elif policy_in.customer_name and policy_in.customer_name.strip():
        # Người dùng nhập thông tin tự do
        full_name = policy_in.customer_name.strip()
        identity = (policy_in.customer_identity or "").strip()
        phone = (policy_in.customer_phone or "").strip()
        email = (policy_in.customer_email or "").strip().lower()

        # Kiểm tra trùng email hoặc CCCD nếu có
        if email:
            customer = db.query(User).filter(User.email == email).first()
        if not customer and identity:
            customer = db.query(User).filter(User.identity_card == identity).first()

        # Tự động tạo hồ sơ khách hàng mới nếu chưa có
        if not customer:
            if not email:
                random_suffix = uuid.uuid4().hex[:6]
                email = f"kh.{identity or random_suffix}@insurtech.vn"

            customer = User(
                email=email,
                hashed_password=hash_password("Customer@123"),
                full_name=full_name,
                phone=phone or None,
                identity_card=identity or None,
                role="customer",
                is_active=True
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)

    if not customer:
        raise HTTPException(
            status_code=400,
            detail="Vui lòng chọn khách hàng có sẵn hoặc nhập thông tin khách hàng thụ hưởng (Họ và tên, CCCD/CMND)."
        )

    product = db.query(InsuranceProduct).filter(InsuranceProduct.id == policy_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Gói bảo hiểm không tồn tại.")

    start = policy_in.start_date or datetime.datetime.utcnow()
    end = policy_in.end_date or (start + datetime.timedelta(days=365))
    policy_num = f"POL-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    sum_insured = policy_in.total_sum_insured if (policy_in.total_sum_insured and policy_in.total_sum_insured > 0) else product.max_coverage_limit
    premium = policy_in.premium_amount if (policy_in.premium_amount and policy_in.premium_amount > 0) else product.base_annual_premium

    new_policy = InsurancePolicy(
        policy_number=policy_num,
        customer_id=customer.id,
        product_id=product.id,
        start_date=start,
        end_date=end,
        total_sum_insured=sum_insured,
        premium_amount=premium,
        payment_cycle=policy_in.payment_cycle,
        status="ACTIVE"
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)

    # Tự động tạo giao dịch nộp phí định kỳ đầu tiên cho hợp đồng mới để đồng bộ với Kế toán & Dashboard
    cycle_name = "Thường niên" if new_policy.payment_cycle == "ANNUALLY" else ("Quý" if new_policy.payment_cycle == "QUARTERLY" else "Tháng")
    initial_payment = PremiumPayment(
        payment_code=f"PAY-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        policy_id=new_policy.id,
        period_name=f"Kỳ 1 ({cycle_name})",
        amount=premium,
        payment_method=policy_in.payment_method or "BANK_TRANSFER",
        payment_date=datetime.datetime.utcnow(),
        status="PAID",
        receipt_image=policy_in.receipt_image
    )
    db.add(initial_payment)
    db.commit()

    res = PolicyResponse.from_orm(new_policy)
    res.customer_name = customer.full_name
    res.product_name = product.product_name
    return res
