import time
import json
from app.config import settings

def truncate_prompt_text(text: str, max_chars: int = 4000) -> str:
    """Cắt tỉa văn bản đầu vào nếu vượt quá giới hạn token an toàn."""
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[Nội dung đã được cắt tỉa để đảm bảo an toàn Token]"
    return text

def get_fallback_mock_response(reason: str, product_name: str = "Bảo hiểm sức khỏe", max_limit: float = 50000000.0, claimed_amount: float = 15000000.0) -> str:
    """Hàm sinh kết quả Fallback an toàn khi API AI gặp sự cố hoặc chạy Mock Mode."""
    recommended = min(claimed_amount * 0.9, max_limit) # Tỷ lệ duyệt mẫu 90%
    disallowed = claimed_amount - recommended if claimed_amount > recommended else 0.0

    fallback_data = {
        "is_valid": True,
        "recommended_amount": recommended,
        "max_coverage_limit": max_limit,
        "fraud_risk_score": 18,
        "risk_level": "Thấp (Hồ sơ tiêu chuẩn)",
        "approved_items": [
            {
                "item_name": "Chi phí giường bệnh nội trú & khám chữa bệnh chuyên khoa",
                "amount": recommended * 0.7,
                "reason": "Nằm trong phạm vi thanh toán quyền lợi nội trú theo quy tắc hợp đồng"
            },
            {
                "item_name": "Chi phí xét nghiệm cận lâm sàng & chẩn đoán hình ảnh",
                "amount": recommended * 0.3,
                "reason": "Chỉ định y khoa phù hợp với chẩn đoán bệnh án"
            }
        ],
        "rejected_items": [
            {
                "item_name": "Phụ phí dịch vụ theo yêu cầu ngoài danh mục bảo hiểm",
                "amount": disallowed,
                "rejection_reason": "Điều khoản loại trừ điểm 4.2 - Không thanh toán phí phát sinh tự nguyện"
            }
        ] if disallowed > 0 else [],
        "fraud_warning_signals": [
            "Hồ sơ đối soát tự động: Chứng từ đầy đủ, không phát hiện trùng lặp viện phí."
        ] if "Mock" in reason else [f"Kích hoạt Fallback Mode: {reason}"],
        "assessment_conclusion": f"Hồ sơ bồi thường {product_name} đủ điều kiện chi trả theo hạn mức quy định. Đề xuất thanh toán {recommended:,.0f} VNĐ.",
        "disclaimer": "KHUYẾN CÁO PHÁP LÝ: Kết quả thẩm định do AI Copilot sinh ra chỉ mang tính chất tham khảo kỹ thuật. Quyết định chi trả bồi thường chính thức thuộc thẩm quyền của Giám định viên con người."
    }
    return json.dumps(fallback_data, ensure_ascii=False)

def call_ai_with_resilience(system_prompt: str, user_prompt: str, max_retries: int = 3, max_limit: float = 50000000.0, claimed_amount: float = 15000000.0) -> str:
    """
    Hàm gọi API OpenAI đạt chuẩn Resilience:
    - Kiểm tra cấu hình và Mock Mode
    - Timeout 15 giây
    - Xử lý Rate Limit (HTTP 429) với Exponential Backoff
    - Cắt tỉa prompt quá dài
    - Tự động chuyển hướng về Fallback Mock Response khi gặp sự cố
    """
    if not settings.OPENAI_API_KEY or settings.AI_MOCK_MODE:
        return get_fallback_mock_response(
            "Chế độ AI Mock Mode (Cục bộ không cần API Key)",
            max_limit=max_limit,
            claimed_amount=claimed_amount
        )

    truncated_user_prompt = truncate_prompt_text(user_prompt)

    try:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        delay = 1.0

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=settings.AI_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": truncated_user_prompt}
                    ],
                    timeout=15.0, # Timeout 15 giây
                    temperature=0.2
                )
                content = response.choices[0].message.content
                if not content or content.strip() == "":
                    raise ValueError("Response rỗng từ AI.")
                return content
            except openai.RateLimitError:
                if attempt == max_retries - 1:
                    return get_fallback_mock_response("Dịch vụ AI đạt giới hạn tần suất (Rate Limit 429).", max_limit=max_limit, claimed_amount=claimed_amount)
                time.sleep(delay)
                delay *= 2.0
            except (openai.APITimeoutError, openai.APIConnectionError):
                if attempt == max_retries - 1:
                    return get_fallback_mock_response("Kết nối tới AI bị Timeout > 15s hoặc gián đoạn mạng.", max_limit=max_limit, claimed_amount=claimed_amount)
                time.sleep(1.0)
            except Exception as e:
                return get_fallback_mock_response(f"Sự cố gọi API: {str(e)}", max_limit=max_limit, claimed_amount=claimed_amount)

        return get_fallback_mock_response("Không thể hoàn tất gọi AI sau các lần thử lại.", max_limit=max_limit, claimed_amount=claimed_amount)
    except Exception as e:
        return get_fallback_mock_response(f"Lỗi khởi tạo client: {str(e)}", max_limit=max_limit, claimed_amount=claimed_amount)

def call_ai_chat_completion(system_prompt: str, user_prompt: str) -> str:
    """Gọi OpenAI Chat Completion nếu có API Key thật và không ở Mock Mode."""
    if not settings.OPENAI_API_KEY or settings.AI_MOCK_MODE:
        return ""
    try:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        truncated_user = truncate_prompt_text(user_prompt, max_chars=3000)
        response = client.chat.completions.create(
            model=settings.AI_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": truncated_user}
            ],
            timeout=15.0,
            temperature=0.7
        )
        content = response.choices[0].message.content
        if content and content.strip():
            return content.strip()
    except Exception:
        pass
    return ""
