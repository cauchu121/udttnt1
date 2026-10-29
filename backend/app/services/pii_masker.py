import re
from sqlalchemy.orm import Session
from app.models import Claim

def mask_pii_sensitive_info(text: str) -> str:
    """Loại bỏ và che mờ thông tin cá nhân PII (CCCD, SĐT, Số thẻ ngân hàng) trước khi gửi sang AI."""
    if not text:
        return ""
    # Che số điện thoại Việt Nam (10 chữ số)
    text = re.sub(r'(\d{3,4})\d{4}(\d{3})', r'\1****\2', text)
    # Che Email cá nhân
    text = re.sub(r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', r'***@\2', text)
    # Che số CCCD / CMND (9 đến 12 chữ số)
    text = re.sub(r'\b\d{9,12}\b', '[REDACTED_NATIONAL_ID]', text)
    # Che số tài khoản ngân hàng hoặc số thẻ (12 đến 19 chữ số)
    text = re.sub(r'\b\d{12,19}\b', '[REDACTED_CARD_NUMBER]', text)
    return text

def prepare_anonymized_claim_context(db: Session, claim: Claim) -> dict:
    """Chuẩn bị ngữ cảnh dữ liệu từ CSDL, đảm bảo nguyên tắc tối thiểu dữ liệu (Data Minimization)."""
    invoices_list = []
    if claim.documents:
        for doc in claim.documents:
            clean_doc_type = mask_pii_sensitive_info(doc.document_type)
            invoices_list.append(f"- {clean_doc_type}: {doc.invoice_amount:,.0f} VNĐ")
    
    invoices_text = "\n".join(invoices_list) if invoices_list else f"- Hóa đơn y tế tổng hợp: {claim.claimed_amount:,.0f} VNĐ"
    clean_diagnosis = mask_pii_sensitive_info(claim.diagnosis or "Không có chẩn đoán cụ thể")
    medical_history = "Khách hàng không ghi nhận tiền sử bệnh lý loại trừ trước đó."

    return {
        "invoices_text": invoices_text,
        "diagnosis": clean_diagnosis,
        "medical_history": medical_history
    }
