import json
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Claim, AILog
from app.schemas import (
    ClaimAssessmentRequest, ClaimAssessmentStrictOutput,
    AdvisorChatRequest, AdvisorChatResponse,
    RiskScoringRequest, RiskScoringResponse
)
from app.auth import get_current_user, require_roles
from app.services.resilient_ai_service import call_ai_with_resilience
from app.services.ai_claim_service import (
    parse_and_validate_ai_json_response,
    generate_chatbot_advice,
    calculate_underwriting_risk
)
from app.services.pii_masker import prepare_anonymized_claim_context

router = APIRouter(prefix="/ai", tags=["Trí tuệ nhân tạo AI Copilot"])

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

@router.post("/claim-assessment", response_model=ClaimAssessmentStrictOutput)
def api_generate_claim_assessment(
    req: ClaimAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "claims_officer"]))
):
    """
    API Thẩm định bồi thường tự động bằng AI Copilot:
    1. Kiểm tra quyền RBAC (chỉ Giám định viên hoặc Admin).
    2. Lấy dữ liệu hồ sơ claim và làm sạch thông tin định danh cá nhân (PII Masking).
    3. Nạp Prompt cấu hình độc lập từ claim_assessment_config.json.
    4. Gọi AI qua Resilient Engine (Timeout 15s, Backoff 429, Fallback Mode).
    5. Parse & Validate kết quả Strict JSON Schema bằng Pydantic.
    6. Lưu bản nháp vào hồ sơ và ghi log hệ thống.
    """
    start_time = time.time()
    claim = db.query(Claim).filter(Claim.id == req.claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ bồi thường.")

    context_data = prepare_anonymized_claim_context(db, claim)
    product_name = claim.policy.product.product_name if (claim.policy and claim.policy.product) else "Gói bảo hiểm chuẩn"
    max_limit = claim.policy.product.max_coverage_limit if (claim.policy and claim.policy.product) else 50000000.0

    # Nạp System Prompt và User Template từ file cấu hình độc lập
    config_path = PROMPTS_DIR / "claim_assessment_config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            system_prompt = cfg["system_prompt"]
            user_template = cfg["user_prompt_template"]
    else:
        system_prompt = "Bạn là Chuyên gia Giám định Bồi thường Bảo hiểm. Trả về đúng định dạng JSON thuần."
        user_template = "Hồ sơ: {diagnosis}, Số tiền: {claimed_amount}"

    user_prompt = user_template.format(
        product_name=product_name,
        max_coverage_limit=max_limit,
        diagnosis=context_data["diagnosis"],
        claimed_amount=claim.claimed_amount,
        invoice_breakdown=context_data["invoices_text"],
        medical_history=context_data["medical_history"]
    )

    # Gọi AI với cơ chế chịu lỗi Resilience
    raw_response = call_ai_with_resilience(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_limit=max_limit,
        claimed_amount=claim.claimed_amount
    )

    # Parse và kiểm duyệt tính toàn vẹn của JSON Output
    validated_output = parse_and_validate_ai_json_response(raw_response, max_limit=max_limit)

    # Lưu bản nháp vào claim để tham khảo (KHÔNG ghi đè approved_amount - Human in the loop)
    claim.fraud_risk_score = validated_output.fraud_risk_score
    claim.ai_assessment_notes = validated_output.assessment_conclusion

    # Ghi log lịch sử gọi AI
    exec_ms = int((time.time() - start_time) * 1000)
    ai_log = AILog(
        user_id=current_user.id,
        feature_name="AI_CLAIM_ASSESSMENT",
        prompt_text=user_prompt[:500],
        response_text=raw_response[:1000],
        execution_time_ms=exec_ms
    )
    db.add(ai_log)
    db.commit()

    return validated_output

@router.post("/chat-advisor", response_model=AdvisorChatResponse)
def api_chat_advisor(
    req: AdvisorChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Chatbot AI tư vấn quyền lợi điều khoản và sản phẩm bảo hiểm 24/7."""
    context = "Hệ thống bảo hiểm cung cấp: Bảo hiểm Sức khỏe Toàn diện (hạn mức 50M), Tai nạn Cá nhân (100M), Bệnh hiểm nghèo (200M). Điểm loại trừ: bệnh có sẵn chưa khai báo, phẫu thuật thẩm mỹ không chỉ định y tế."
    if req.policy_id:
        policy = db.query(Claim).filter(Claim.policy_id == req.policy_id).first()
        if policy and policy.policy and policy.policy.product:
            context += f"\nHợp đồng hiện tại: {policy.policy.product.product_name}, Điều khoản: {policy.policy.product.terms_and_conditions}"

    return generate_chatbot_advice(req.message, policy_context=context)

@router.post("/risk-scorer", response_model=RiskScoringResponse)
def api_risk_scorer(
    req: RiskScoringRequest,
    current_user: User = Depends(require_roles(["admin", "claims_officer"]))
):
    """AI phân tích chỉ số định lượng ẩn danh để chấm điểm nguy cơ rủi ro định phí hợp đồng."""
    return calculate_underwriting_risk(
        age_group=req.age_group,
        claim_ratio=req.claim_ratio,
        job_category=req.job_category,
        risk_notes=req.risk_notes or "Bình thường"
    )
