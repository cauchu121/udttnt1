import json
from pydantic import ValidationError
from app.schemas import ClaimAssessmentStrictOutput, AdvisorChatResponse, RiskScoringResponse
from app.services.resilient_ai_service import call_ai_with_resilience

def parse_and_validate_ai_json_response(raw_text: str, max_limit: float) -> ClaimAssessmentStrictOutput:
    """Làm sạch và Parse JSON từ phản hồi thô của AI, áp dụng ràng buộc cứng bảo vệ ngân sách."""
    clean_text = raw_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()

    try:
        data = json.loads(clean_text)
        validated = ClaimAssessmentStrictOutput(**data)

        # Ràng buộc cứng: Số tiền duyệt tuyệt đối không vượt quá hạn mức tối đa
        if validated.recommended_amount > max_limit:
            validated.recommended_amount = max_limit
            validated.fraud_warning_signals.append(
                "Cảnh báo hệ thống: Số tiền AI đề xuất ban đầu vượt hạn mức, đã tự động điều chỉnh về hạn mức trần."
            )
        return validated
    except (json.JSONDecodeError, ValidationError) as e:
        # Fallback an toàn nếu AI trả JSON lỗi
        return ClaimAssessmentStrictOutput(
            is_valid=True,
            recommended_amount=min(max_limit * 0.5, 10000000.0),
            max_coverage_limit=max_limit,
            fraud_risk_score=50,
            risk_level="Cần giám định viên xem xét thủ công",
            approved_items=[],
            rejected_items=[],
            fraud_warning_signals=[f"Dữ liệu phản hồi AI không đúng định dạng schema: {str(e)}"],
            assessment_conclusion="Đề xuất giám định thủ công để đảm bảo tính chuẩn xác.",
            disclaimer="LƯU Ý: Đã kích hoạt chế độ thẩm định an toàn dự phòng."
        )

def generate_expert_insurance_advisor_reply(user_query: str, policy_context: str = ""):
    """
    Knowledge Engine chuyên sâu của Trợ lý Ảo InsurTech:
    Cung cấp câu trả lời chuẩn mực như Chuyên gia Tư vấn Bảo hiểm Cấp cao (Senior Insurance Specialist),
    hỗ trợ nhận diện đa dạng từ ngữ, từ lóng, viết tắt và kèm câu hỏi gợi ý tiếp theo.
    """
    import re
    q = user_query.lower().strip()

    # 1. Phẫu thuật thẩm mỹ, chỉnh hình & làm đẹp
    if any(k in q for k in ["thẩm mỹ", "tham my", "làm đẹp", "lam dep", "nâng mũi", "nang mui", "cắt mí", "cat mi", "hút mỡ", "hut mo", "filler", "botox", "nha khoa thẩm mỹ", "xăm", "trị mụn", "tri mun"]):
        reply = (
            "Kính chào Quý khách! Về quyền lợi phẫu thuật thẩm mỹ và tạo hình, Chuyên gia InsurTech xin giải đáp chi tiết như sau:\n\n"
            "🎯 1. Kết luận thẩm định:\n"
            "Các thủ thuật phẫu thuật thẩm mỹ, chỉnh hình tự nguyện (như nâng mũi, cắt mí, hút mỡ bụng, tiêm filler, niềng răng, bọc răng sứ thẩm mỹ...) thuộc ĐIỂM LOẠI TRỪ TUYỆT ĐỐI của tất cả các gói bảo hiểm sức khỏe (Quy tắc điều khoản 4.2). Chi phí này KHÔNG ĐƯỢC BỒI THƯỜNG.\n\n"
            "📜 2. Trường hợp ngoại lệ duy nhất được thanh toán:\n"
            "• Phẫu thuật tái tạo mô hoặc chỉnh hình phục hồi chức năng do di chứng của TAI NẠN (giao thông, sinh hoạt) xảy ra trong thời hạn bảo hiểm.\n"
            "• Phẫu thuật tái tạo mô sau điều trị cắt bỏ khối u ác tính (ung thư) hoặc bỏng nặng độ 3 trở lên, có chỉ định y khoa bắt buộc từ bác sĩ chuyên khoa.\n\n"
            "⚠️ 3. Điều kiện cần chuẩn bị:\n"
            "Nếu thuộc diện ngoại lệ do tai nạn, Quý khách cần có Bệnh án phẫu thuật ghi rõ tổn thương do tai nạn và Hóa đơn GTGT viện phí hợp pháp.\n\n"
            "💡 Lời khuyên chuyên gia: Quý khách hãy giữ lại đầy đủ Giấy ra viện và Bảng kê chi phí để gửi thẩm định bồi thường online trên hệ thống!"
        )
        suggests = [
            "Thời gian chờ bệnh hiểm nghèo?",
            "Gãy xương do tai nạn bồi thường thế nào?",
            "Hồ sơ bồi thường cần giấy tờ gì?",
            "Hạn mức viện phí phẫu thuật nội trú?"
        ]
        return reply, suggests

    # 2. Thời gian chờ bệnh hiểm nghèo, bệnh thông thường & tai nạn
    if (any(k in q for k in ["thời gian chờ", "thoi gian cho", "chờ bao lâu", "cho bao lau", "bao lâu thì được", "bao lau thi duoc", "mấy ngày thì được", "may ngay thi duoc"]) or (
        any(k in q for k in ["bao lâu", "mấy tháng", "khi nào được"]) and any(k in q for k in ["hiểm nghèo", "ung thư", "tai biến", "đột quỵ", "bệnh"])
    )) and not any(k in q for k in ["ân hạn", "an han", "đóng phí", "dong phi", "thu phí"]):
        reply = (
            "Kính chào Quý khách! Về quy định Thời Gian Chờ (Waiting Period) - khoảng thời gian hợp đồng chưa phát sinh trách nhiệm bồi thường:\n\n"
            "⏳ 1. Biểu thời gian chờ chuẩn của hệ thống InsurTech:\n"
            "• Rủi ro do Tai nạn: 0 NGÀY (Hiệu lực bảo vệ tức thì sau 24h kích hoạt hợp đồng).\n"
            "• Bệnh thông thường (Viêm ruột thừa, sốt xuất huyết, viêm phổi...): 30 NGÀY kể từ ngày cấp đơn.\n"
            "• Bệnh hiểm nghèo (Ung thư, Đột quỵ, Nhồi máu cơ tim, Suy thận...): 90 NGÀY. Người được bảo hiểm phải còn sống tối thiểu 30 ngày kể từ ngày có chẩn đoán xác định.\n"
            "• Bệnh đặc biệt & Bệnh mãn tính (Sỏi thận, trĩ, viêm xoang, polyp, nang giáp...): 120 đến 365 NGÀY (1 năm).\n"
            "• Quyền lợi Thai sản: 270 NGÀY (9 tháng) tính đến ngày chuyển dạ sinh con.\n\n"
            "⚠️ 2. Lưu ý chuyên gia:\n"
            "Các triệu chứng hoặc chẩn đoán khởi phát trong thời gian chờ sẽ không được chi trả và có thể bị coi là bệnh có sẵn cho các kỳ tái tục tiếp theo.\n\n"
            "💡 Lời khuyên chuyên gia: Quý khách nên tham gia bảo hiểm sớm khi sức khỏe còn tốt để vượt qua thời gian chờ an toàn!"
        )
        suggests = [
            "Bệnh có sẵn có được chi trả không?",
            "Ung thư giai đoạn đầu có được bồi thường?",
            "Quyền lợi thai sản sinh đẻ?",
            "Gói bảo hiểm sức khỏe tối ưu?"
        ]
        return reply, suggests

    # 3. Bệnh hiểm nghèo & Ung thư (Critical Illness & Cancer)
    if any(k in q for k in ["hiểm nghèo", "hiem ngheo", "ung thư", "ung thu", "k gan", "k phổi", "k vú", "xạ trị", "xa tri", "hóa trị", "hoa tri", "nhồi máu cơ tim", "nhoi mau co tim", "đột quỵ", "dot quy", "tai biến", "tai bien", "suy thận", "suy than"]):
        reply = (
            "Kính chào Quý khách! Về quyền lợi bảo hiểm Bệnh Hiểm Nghèo & Ung Thư:\n\n"
            "🎯 1. Cơ chế chi trả tài chính:\n"
            "• Khoán tiền mặt một lần (Lump sum): Gói 'Bảo hiểm Bệnh Hiểm Nghèo Vững Tâm' cam kết chi trả 100% hạn mức (lên tới 200.000.000 VNĐ) ngay khi có kết quả sinh thiết giải phẫu bệnh xác định bệnh hiểm nghèo thuộc danh mục.\n"
            "• Hỗ trợ chi phí điều trị: Gói 'Bảo hiểm Sức khỏe Phúc An Toàn Diện' (50.000.000 VNĐ/năm) tiếp tục thanh toán tiền giường, phẫu thuật khối u, hóa trị và xạ trị theo viện phí thực tế.\n\n"
            "⚠️ 2. Điều kiện hưởng quyền lợi:\n"
            "• Vượt qua thời gian chờ 90 ngày kể từ ngày hợp đồng có hiệu lực.\n"
            "• Bệnh nhân còn sống tối thiểu 30 ngày kể từ ngày có chẩn đoán xác định từ bệnh viện chuyên khoa ung bướu.\n"
            "• Không thuộc các điểm loại trừ về bệnh có sẵn chưa kê khai trung thực.\n\n"
            "💡 Lời khuyên chuyên gia: Quý khách hãy yêu cầu Bệnh viện cung cấp đầy đủ Kết quả giải phẫu bệnh lý (sinh thiết) và Bệnh án chi tiết để nộp hồ sơ claim trực tuyến!"
        )
        suggests = [
            "Thời gian chờ bệnh hiểm nghèo?",
            "Hồ sơ bồi thường cần giấy tờ gì?",
            "Bệnh có sẵn được chi trả không?",
            "Tư vấn gói bảo hiểm tuổi 32?"
        ]
        return reply, suggests

    # 4. Mua nhiều hợp đồng bảo hiểm cùng lúc (Trùng bảo hiểm / Thanh toán kép)
    if any(k in q for k in ["nhiều bảo hiểm", "nhieu bao hiem", "trùng", "trung", "2 bảo hiểm", "2 th?", "2 thẻ", "công ty khác", "bảo hiểm y tế", "bhyt", "thanh toán kép", "thanh toan kep", "đền bù gấp đôi", "thanh toán gấp đôi", "gấp đôi", "gap doi"]):
        reply = (
            "Kính chào Quý khách! Về nguyên tắc khi sở hữu Nhiều Hợp Đồng Bảo Hiểm hoặc có thêm BHYT Nhà nước:\n\n"
            "⚖️ 1. Đối với chi phí Viện phí khám chữa bệnh (Nguyên tắc Bồi hoàn thực tế):\n"
            "• Quý khách không được thanh toán vượt quá số tiền thực tế ghi trên hóa đơn bệnh viện.\n"
            "• Tuy nhiên, nếu BHYT Nhà nước hoặc một công ty bảo hiểm khác đã chi trả một phần, InsurTech sẽ tiếp tục thanh toán phần chi phí chênh lệch còn lại mà Quý khách phải bỏ tiền túi!\n\n"
            "💰 2. Đối với Bệnh Hiểm Nghèo & Tai Nạn (Nguyên tắc Khoán tiền mặt):\n"
            "• ĐƯỢC HƯỞNG ĐỘC LẬP TỪ TẤT CẢ CÁC HỢP ĐỒNG! Nếu Quý khách có 2 gói bệnh hiểm nghèo tại 2 công ty khác nhau, cả 2 nơi đều sẽ chi trả 100% tiền mặt theo mệnh giá cam kết.\n\n"
            "💡 Lời khuyên chuyên gia: Kết hợp song song BHYT Nhà nước và Bảo hiểm InsurTech là giải pháp tối ưu giúp Quý khách gần như không phải chi trả thêm bất kỳ viện phí nào!"
        )
        suggests = [
            "Gói bệnh hiểm nghèo hạn mức bao nhiêu?",
            "Bảo hiểm tai nạn chi trả thế nào?",
            "Hồ sơ claim bồi thường cần gì?",
            "Thẻ bảo lãnh viện phí dùng ở đâu?"
        ]
        return reply, suggests

    # 5. Trẻ em & Gói bảo hiểm gia đình
    if any(k in q for k in ["trẻ em", "tre em", "con nít", "con nit", "em bé", "em be", "bé ", "bé,", "cho bé", "cho be", "trẻ sơ sinh", "tre so sinh", "con nhỏ", "con nho", "mua cho con", "cho con"]):
        reply = (
            "Kính chào Quý khách! Về giải pháp bảo hiểm sức khỏe cho Trẻ Em & Gia Đình:\n\n"
            "👶 1. Điều kiện tham gia:\n"
            "Trẻ em từ 15 ngày tuổi đến 18 tuổi có thể tham gia gói 'Bảo hiểm Sức khỏe Phúc An Toàn Diện' (kèm theo hợp đồng của bố hoặc mẹ).\n\n"
            "🛡️ 2. Quyền lợi thiết thực cho bé:\n"
            "• Chi trả 100% viện phí nội trú cho các bệnh hô hấp phổ biến (viêm phế quản phổi, viêm tai giữa, sốt co giật, tay chân miệng, tiêu chảy cấp).\n"
            "• Hạn mức tiền giường 2.500.000 VNĐ/ngày giúp bé được nằm phòng dịch vụ tiêu chuẩn, yên tĩnh cùng bố mẹ.\n"
            "• Hỗ trợ quyền lợi ngoại trú cho các đợt khám và xét nghiệm nhanh trong ngày.\n\n"
            "💡 Lời khuyên chuyên gia: Trẻ dưới 6 tuổi sức đề kháng còn non nớt, Quý khách nên chọn gói có bao gồm quyền lợi Khám Ngoại Trú để an tâm đưa bé đi khám bất kỳ lúc nào!"
        )
        suggests = [
            "Hồ sơ claim cho trẻ em cần giấy gì?",
            "Thời gian chờ bệnh hô hấp cho bé?",
            "Tư vấn gói bảo hiểm gia đình?",
            "Phí bảo hiểm cho bé 3 tuổi?"
        ]
        return reply, suggests

    # 6. Nằm viện, viện phí & tiền phòng nội trú
    if any(k in q for k in ["nằm viện", "nam vien", "nội trú", "noi tru", "ngoại trú", "ngoai tru", "tiền giường", "tien giuong", "tiền phòng", "tien phong", "viện phí", "vien phi", "phòng dịch vụ", "bv tư", "vinmec", "fv"]) and not any(k in q for k in ["ruột thừa", "sỏi", "nha khoa", "răng", "mắt"]):
        reply = (
            "Kính chào Quý khách! Về quyền lợi Viện Phí Nội Trú và Tiền Giường bệnh:\n\n"
            "🏥 1. Điều kiện điều trị nội trú:\n"
            "Người được bảo hiểm phải nhập viện điều trị theo chỉ định y khoa của bác sĩ và lưu viện qua đêm tối thiểu 24 giờ.\n\n"
            "💰 2. Hạn mức chi trả cụ thể:\n"
            "• Tiền giường & phòng dịch vụ: Thanh toán tối đa 2.500.000 VNĐ/ngày (áp dụng cho cả bệnh viện công lập và các bệnh viện tư nhân/quốc tế như Vinmec, FV, Hoàn Mỹ).\n"
            "• Chi phí phẫu thuật: Chi trả 100% chi phí mổ mở hoặc nội soi, phòng mổ, thuốc gây mê và vật tư tiêu hao.\n"
            "• Thuốc men & cận lâm sàng: Thanh toán toàn bộ thuốc kê đơn và xét nghiệm chẩn đoán trong thời gian nằm viện.\n"
            "• Tổng hạn mức hàng năm: 50.000.000 VNĐ đối với gói Sức khỏe Phúc An Toàn Diện.\n\n"
            "⚠️ 3. Điều trị ngoại trú trong ngày:\n"
            "Hạn mức phụ tối đa 1.500.000 VNĐ/lần khám (tối đa 10 lần/năm) cho các ca khám điều trị trong ngày không lưu viện qua đêm.\n\n"
            "💡 Lời khuyên chuyên gia: Khi xuất viện, hãy yêu cầu Bệnh viện xuất Hóa đơn điện tử GTGT kèm Bảng kê viện phí chi tiết để việc duyệt claim được xử lý tức thì!"
        )
        suggests = [
            "Mổ ruột thừa viện phí bao nhiêu?",
            "Thẻ bảo lãnh viện phí dùng thế nào?",
            "Hồ sơ claim bồi thường cần gì?",
            "Gói bảo hiểm sức khỏe tối ưu?"
        ]
        return reply, suggests

    # 5. Tai nạn thương tích, gãy xương & chấn thương
    if any(k in q for k in ["tai nạn", "tai nan", "gãy tay", "gay tay", "gãy chân", "gay chan", "gãy xương", "gay xuong", "bó bột", "bo bot", "mổ nẹp", "bắt vít", "bat vit", "ngã", "nga", "chấn thương", "chan thuong", "va chạm", "ngã xe", "nga xe"]):
        reply = (
            "Kính chào Quý khách! Về quyền lợi khi xảy ra sự kiện Tai Nạn Thương Tích:\n\n"
            "⚡ 1. Hiệu lực bảo vệ tức thì:\n"
            "Hợp đồng bảo hiểm tai nạn KHÔNG ÁP DỤNG THỜI GIAN CHỜ - quyền lợi có hiệu lực ngay sau 24h kích hoạt đơn bảo hiểm.\n\n"
            "🛡️ 2. Các quyền lợi được chi trả:\n"
            "• Chi phí y tế cấp cứu: Thanh toán 100% viện phí thực tế cho phẫu thuật chỉnh hình, nẹp vít, bó bột, thuốc men và xét nghiệm hình ảnh (X-quang, CT Scan).\n"
            "• Trợ cấp nằm viện do tai nạn: 300.000 VNĐ/ngày lưu viện.\n"
            "• Bồi thường thương tật theo Biểu tỷ lệ Bộ Tài chính: Hạn mức tối đa 100.000.000 VNĐ (Ví dụ: Gãy xương cẳng tay chi trả từ 15% đến 25% hạn mức = 15 - 25 triệu VNĐ).\n\n"
            "⚠️ 3. Điểm loại trừ cần lưu ý:\n"
            "Tai nạn phát sinh do vi phạm nồng độ cồn khi điều khiển phương tiện, sử dụng chất kích thích hoặc tham gia ẩu đả sẽ BỊ TỪ CHỐI bồi thường.\n\n"
            "💡 Lời khuyên chuyên gia: Quý khách hãy chụp lại Giấy chứng nhận thương tích hoặc Phim X-quang kèm Hóa đơn viện phí để nộp claim online nhé!"
        )
        suggests = [
            "Hồ sơ bồi thường tai nạn cần gì?",
            "Thời gian duyệt claim bồi thường?",
            "Hạn mức viện phí phẫu thuật?",
            "Tư vấn gói bảo hiểm tai nạn 100M?"
        ]
        return reply, suggests

    # 6. Bệnh cấp tính thông thường (Sốt xuất huyết, Viêm phổi, Cúm A, Ngộ độc thực phẩm)
    if any(k in q for k in ["sốt xuất huyết", "sot xuat huyet", "viêm phổi", "viem phoi", "viêm phế quản", "viem phe quan", "ngộ độc", "ngo doc", "cúm a", "cum a", "tiêu chảy", "tieu chay", "truyền dịch", "truyen dich"]):
        reply = (
            "Kính chào Quý khách! Về quyền lợi điều trị các bệnh lý cấp tính thông thường (Sốt xuất huyết, Cúm A, Viêm phổi, Ngộ độc...):\n\n"
            "🎯 1. Khả năng chi trả:\n"
            "Được bồi thường 100% chi phí điều trị nội trú sau khi hợp đồng đã vượt qua 30 ngày thời gian chờ.\n\n"
            "💰 2. Các khoản mục được thanh toán:\n"
            "• Tiền giường bệnh nội trú theo hạn mức (lên đến 2.500.000 VNĐ/ngày).\n"
            "• Dịch truyền, kháng sinh, thuốc hạ sốt, xét nghiệm tiểu cầu, công thức máu và chi phí chăm sóc y tế.\n"
            "• Nếu chỉ khám và truyền dịch ngoại trú trong ngày: Chi trả theo hạn mức khám ngoại trú (tối đa 1.500.000 VNĐ/đợt).\n\n"
            "💡 Lời khuyên chuyên gia: Khi bác sĩ chỉ định lưu viện điều trị, Quý khách hãy nhắc bệnh viện cấp Giấy ra viện có ghi rõ ngày giờ vào và xuất viện để bảo hiểm chi trả trọn vẹn số ngày giường nằm!"
        )
        suggests = [
            "Hạn mức tiền giường nội trú bao nhiêu?",
            "Thời gian chờ bệnh thông thường?",
            "Hồ sơ bồi thường cần giấy tờ gì?",
            "Bảo hiểm cho trẻ nhỏ có gói nào?"
        ]
        return reply, suggests

    # 7. Phẫu thuật thông thường (Ruột thừa, Sỏi thận, Mổ nội soi, Trĩ, Thoát vị)
    if any(k in q for k in ["ruột thừa", "ruot thua", "sỏi thận", "soi than", "tán sỏi", "tan soi", "mổ nội soi", "mo noi soi", "phẫu thuật", "phau thuat", "mổ trĩ", "mo tri", "thoát vị", "thoat vi"]):
        reply = (
            "Kính chào Quý khách! Về chi phí phẫu thuật bệnh lý (như mổ ruột thừa cấp, tán sỏi thận, mổ trĩ, thoát vị đĩa đệm...):\n\n"
            "🎯 1. Phân loại theo thời gian chờ:\n"
            "• Viêm ruột thừa cấp: Là bệnh cấp cứu, được chi trả 100% sau 30 NGÀY thời gian chờ.\n"
            "• Sỏi thận, sỏi mật, trĩ, thoát vị đĩa đệm: Thuộc nhóm Bệnh đặc biệt, áp dụng thời gian chờ từ 120 đến 365 NGÀY (1 năm).\n\n"
            "💰 2. Các chi phí được phê duyệt:\n"
            "• Chi phí phòng mổ, công phẫu thuật của phẫu thuật viên, thuốc gây mê hồi sức.\n"
            "• Vật tư y tế tiêu hao (dao mổ nội soi, clip kẹp, dịch truyền).\n"
            "• Tiền giường nằm phòng hậu phẫu và điều trị nội trú.\n\n"
            "⚠️ 3. Lưu ý: Không chi trả cho các dịch vụ tự nguyện theo yêu cầu cá nhân (như chỉ định đích danh viện trưởng mổ ngoài giờ, phòng chăm sóc đặc biệt VIP vượt hạn mức).\n\n"
            "💡 Lời khuyên chuyên gia: Hãy xin Bảng kê chi tiết viện phí (Mẫu số 01/BV hoặc 02/BV) từ bệnh viện để nộp claim nhanh nhất!"
        )
        suggests = [
            "Hạn mức chi trả phẫu thuật tối đa?",
            "Hồ sơ claim bồi thường cần gì?",
            "Thời gian chờ bệnh đặc biệt bao lâu?",
            "Thẻ bảo lãnh viện phí dùng ở đâu?"
        ]
        return reply, suggests

    # 8. Thai sản, Sinh đẻ & Khám thai
    if any(k in q for k in ["thai sản", "thai san", "sinh đẻ", "sinh de", "sinh con", "mổ đẻ", "mo de", "khám thai", "kham thai", "sinh thường", "sinh thuong", "bầu bí", "mang thai"]):
        reply = (
            "Kính chào Quý khách! Về quyền lợi Thai sản & Sinh đẻ tại InsurTech:\n\n"
            "⏳ 1. Điều kiện thời gian chờ:\n"
            "Thời gian chờ thai sản quy định là 270 NGÀY (khoảng 9 tháng) kể từ ngày ký hợp đồng có hiệu lực đến ngày chuyển dạ sinh con.\n\n"
            "💰 2. Hạn mức chi trả:\n"
            "• Sinh thường: Thanh toán trọn gói lên tới 15.000.000 VNĐ.\n"
            "• Sinh mổ (do chỉ định y khoa): Thanh toán lên tới 30.000.000 VNĐ bao gồm chi phí phòng mổ, gây tê tủy sống và viện phí lưu viện 4-5 ngày.\n"
            "• Cấp cứu biến chứng thai sản: Thanh toán 100% theo viện phí cấp cứu (thai ngoài tử cung, dọa sảy thai, tiền sản giật).\n\n"
            "💡 Lời khuyên chuyên gia: Nếu Quý khách đang lên kế hoạch có em bé, hãy tham gia gói bảo hiểm trước khi mang thai ít nhất 1 tháng để đảm bảo đủ 270 ngày chờ nhé!"
        )
        suggests = [
            "Bảo hiểm cho trẻ sơ sinh có gói nào?",
            "Thời gian chờ các bệnh khác?",
            "Hồ sơ claim thai sản gồm những gì?",
            "Bảo lãnh viện phí bệnh viện phụ sản?"
        ]
        return reply, suggests

    # 9. Trẻ em & Gói bảo hiểm gia đình
    if any(k in q for k in ["trẻ em", "tre em", "con nít", "con nit", "em bé", "em be", "trẻ sơ sinh", "tre so sinh", "con nhỏ", "con nho", "mua cho con", "mua cho bé", "cho con"]):
        reply = (
            "Kính chào Quý khách! Về giải pháp bảo hiểm sức khỏe cho Trẻ Em & Gia Đình:\n\n"
            "👶 1. Điều kiện tham gia:\n"
            "Trẻ em từ 15 ngày tuổi đến 18 tuổi có thể tham gia gói 'Bảo hiểm Sức khỏe Phúc An Toàn Diện' (kèm theo hợp đồng của bố hoặc mẹ).\n\n"
            "🛡️ 2. Quyền lợi thiết thực cho bé:\n"
            "• Chi trả 100% viện phí nội trú cho các bệnh hô hấp phổ biến (viêm phế quản phổi, viêm tai giữa, sốt co giật, tay chân miệng, tiêu chảy cấp).\n"
            "• Hạn mức tiền giường 2.500.000 VNĐ/ngày giúp bé được nằm phòng dịch vụ tiêu chuẩn, yên tĩnh cùng bố mẹ.\n"
            "• Hỗ trợ quyền lợi ngoại trú cho các đợt khám và xét nghiệm nhanh trong ngày.\n\n"
            "💡 Lời khuyên chuyên gia: Trẻ dưới 6 tuổi sức đề kháng còn non nớt, Quý khách nên chọn gói có bao gồm quyền lợi Khám Ngoại Trú để an tâm đưa bé đi khám bất kỳ lúc nào!"
        )
        suggests = [
            "Hồ sơ claim cho trẻ em cần giấy gì?",
            "Thời gian chờ bệnh hô hấp cho bé?",
            "Tư vấn gói bảo hiểm gia đình?",
            "Phí bảo hiểm cho bé 3 tuổi?"
        ]
        return reply, suggests

    # 10. Gợi ý gói bảo hiểm theo độ tuổi & nghề nghiệp
    if any(k in q for k in ["tuổi", "tuoi", "gói nào", "goi nao", "nên chọn", "nen chon", "tư vấn gói", "tu van goi", "gợi ý", "goi y", "văn phòng", "van phong", "xây dựng", "xay dung", "công nhân"]):
        import re
        age_match = re.search(r"(\d{1,2})\s*tuổi", q) or re.search(r"tuổi\s*(\d{1,2})", q)
        age_str = f"độ tuổi {age_match.group(1)}" if age_match else "độ tuổi của bạn"
        reply = (
            f"Kính chào Quý khách! Căn cứ vào {age_str} và môi trường làm việc thực tế, Chuyên gia InsurTech đề xuất giải pháp tối ưu như sau:\n\n"
            "🥇 1. Gói nền tảng cốt lõi: 'Bảo hiểm Sức khỏe Phúc An Toàn Diện'\n"
            "• Hạn mức bảo vệ: 50.000.000 VNĐ/năm.\n"
            "• Mức phí thường niên: Chỉ từ 3.200.000 VNĐ/năm (~8.700 VNĐ/ngày).\n"
            "• Quyền lợi nổi bật: Thanh toán viện phí phẫu thuật, nằm viện phòng dịch vụ, thuốc men và xét nghiệm cận lâm sàng.\n\n"
            "🥈 2. Gói dự phòng tài chính: 'Bảo hiểm Bệnh Hiểm Nghèo Vững Tâm'\n"
            "• Hạn mức bảo vệ: 200.000.000 VNĐ tiền mặt ngay khi có chẩn đoán xác định.\n"
            "• Phí chỉ từ 2.000.000 VNĐ/năm nếu tham gia ở độ tuổi trẻ.\n\n"
            "🥉 3. Gói rủi ro nghề nghiệp: 'Bảo hiểm Tai Nạn Cá Nhân Toàn Diện' (Hạn mức 100M, phí chỉ 2M/năm) đặc biệt phù hợp nếu bạn thường xuyên di chuyển hoặc làm việc ngoài trời.\n\n"
            "💡 Bạn có thể bấm vào tab 'Gói Sản Phẩm' ở menu bên trái để so sánh chi tiết bảng quyền lợi và biểu phí!"
        )
        suggests = [
            "Hạn mức viện phí phẫu thuật nội trú?",
            "Thời gian chờ bệnh hiểm nghèo?",
            "Thủ tục cấp hợp đồng bảo hiểm mới?",
            "Đóng phí theo năm hay theo quý?"
        ]
        return reply, suggests

    # 11. Bệnh có sẵn (Pre-existing Conditions) & Kê khai trung thực
    if any(k in q for k in ["bệnh có sẵn", "benh co san", "tiền sử", "tien su", "kê khai", "ke khai", "viêm gan b", "viem gan b", "huyết áp", "huyet ap", "dạ dày", "da day", "nang giáp", "nang giap", "tiểu đường", "tieu duong", "giấu bệnh"]):
        reply = (
            "Kính chào Quý khách! Về quy tắc Bệnh Có Sẵn (Pre-existing Conditions) và nghĩa vụ Kê Khai Trung Thực:\n\n"
            "⚖️ 1. Khái niệm bệnh có sẵn:\n"
            "Là bất kỳ bệnh tật hoặc thương tật nào đã được chẩn đoán, có triệu chứng hoặc đã được điều trị y tế trước ngày nộp hồ sơ bảo hiểm.\n\n"
            "📋 2. Chính sách thẩm định của InsurTech:\n"
            "• Nếu Quý khách kê khai trung thực: Công ty có thể chấp thuận bảo hiểm với điều kiện thời gian chờ 365 ngày đối với bệnh có sẵn đó, hoặc tăng phí nhẹ. Các bệnh lý mới phát sinh khác VẪN ĐƯỢC BẢO VỆ 100%.\n"
            "• Nếu cố tình không kê khai (giấu bệnh): Doanh nghiệp bảo hiểm có quyền đơn phương chấm dứt hợp đồng và TỪ CHỐI CHI TRẢ BỒI THƯỜNG khi phát hiện lịch sử y khoa cũ.\n\n"
            "💡 Lời khuyên chuyên gia: Hãy luôn kê khai trung thực tất cả tiền sử bệnh án khi tham gia để hợp đồng có giá trị bảo vệ pháp lý vững chắc nhất!"
        )
        suggests = [
            "Điểm loại trừ bảo hiểm gồm những gì?",
            "Thời gian chờ bệnh đặc biệt bao lâu?",
            "Thủ tục cấp hợp đồng mới?",
            "Hồ sơ claim bồi thường cần gì?"
        ]
        return reply, suggests

    # 12. Bảo lãnh viện phí trực tiếp (Direct Billing / Thẻ xanh)
    if any(k in q for k in ["bảo lãnh", "bao lanh", "thẻ bảo lãnh", "the bao lanh", "thẻ xanh", "the xanh", "không cần trả tiền", "khong can tra tien", "liên kết", "lien ket", "bệnh viện liên kết"]):
        reply = (
            "Kính chào Quý khách! Dịch vụ Bảo Lãnh Viện Phí Trực Tiếp (Direct Billing) tại InsurTech:\n\n"
            "💳 1. Tiện ích vượt trội:\n"
            "Quý khách không cần tự chi trả tiền túi trước rồi mới nộp hồ sơ đòi bồi thường. Công ty bảo hiểm sẽ thanh toán viện phí trực tiếp cho Bệnh viện liên kết.\n\n"
            "🏥 2. Quy trình 3 bước sử dụng:\n"
            "• Bước 1: Khi nhập viện, xuất trình CCCD và Thẻ bảo hiểm điện tử tại Quầy Bảo hiểm / Thu ngân của bệnh viện liên kết.\n"
            "• Bước 2: Bệnh viện gửi dự toán viện phí qua hệ thống API InsurTech AI.\n"
            "• Bước 3: Hệ thống duyệt bảo lãnh tự động trong vòng 30 - 60 phút. Khi xuất viện, Quý khách chỉ cần thanh toán phần chi phí ngoài phạm vi bảo hiểm (nếu có).\n\n"
            "💡 Lời khuyên chuyên gia: Mạng lưới InsurTech liên kết hơn 300 bệnh viện uy tín (Bạch Mai, Việt Đức, Chợ Rẫy, ĐH Y Dược, Vinmec, FV...)."
        )
        suggests = [
            "Hạn mức tiền giường nằm viện bao nhiêu?",
            "Nằm viện công có bảo lãnh không?",
            "Hồ sơ claim nếu không có bảo lãnh?",
            "Thời gian chờ bệnh thông thường?"
        ]
        return reply, suggests

    # 13. Hồ sơ, thủ tục và chứng từ bồi thường (Claim)
    if any(k in q for k in ["hồ sơ", "ho so", "chứng từ", "chung tu", "hóa đơn", "hoa don", "thủ tục", "thu tuc", "giấy tờ", "giay to", "cần những gì", "quy trình claim", "nộp claim", "thời hạn nộp"]):
        reply = (
            "Kính chào Quý khách! Bộ hồ sơ yêu cầu bồi thường (Claim) tại InsurTech AI gồm 4 nhóm chứng từ chính:\n\n"
            "📋 1. Danh mục chứng từ bắt buộc:\n"
            "1. Chứng từ y tế điều trị: Giấy ra viện, Trích sao bệnh án hoặc Giấy chứng nhận phẫu thuật (có mộc tròn của bệnh viện).\n"
            "2. Chứng từ tài chính: Hóa đơn điện tử GTGT hoặc Biên lai thu viện phí kèm Bảng kê chi phí khám chữa bệnh (Mẫu 01/BV hoặc 02/BV).\n"
            "3. Bằng chứng chẩn đoán: Kết quả xét nghiệm máu, phiếu chụp X-quang, MRI, CT Scan, kết quả giải phẫu bệnh.\n"
            "4. Giấy tờ định danh: Số CCCD người được bảo hiểm và Số hợp đồng hiệu lực.\n\n"
            "📌 2. Thời hạn nộp hồ sơ:\n"
            "Trong vòng 60 NGÀY kể từ ngày xuất viện.\n\n"
            "🚀 3. Tốc độ giải quyết:\n"
            "Quý khách bấm ngay nút 'Nộp Hồ Sơ Claim' ở góc trên bên phải để nộp online. Máy chủ AI sẽ đối soát tự động trong 30 giây và Giám định viên duyệt chi trả trong 24h làm việc!"
        )
        suggests = [
            "Nộp hồ sơ claim online ở đâu?",
            "Bị từ chối claim thì làm thế nào?",
            "Hạn mức tiền giường nội trú?",
            "Thời gian chờ bệnh hiểm nghèo?"
        ]
        return reply, suggests

    # 14. Lý do từ chối bồi thường & Khiếu nại (Rejection & Appeal)
    if any(k in q for k in ["từ chối", "tu choi", "bị bác", "bi bac", "không được đền", "khong duoc den", "khiếu nại", "khieu nai", "phúc khảo", "phuc khao", "tại sao từ chối"]):
        reply = (
            "Kính chào Quý khách! Về các trường hợp từ chối bồi thường và Quyền Khiếu nại của khách hàng:\n\n"
            "❌ 1. 4 nguyên nhân từ chối claim phổ biến nhất:\n"
            "1. Sự kiện bệnh lý xảy ra trong Thời gian chờ.\n"
            "2. Bệnh có sẵn trước khi ký hợp đồng nhưng không kê khai trung thực.\n"
            "3. Khoản mục viện phí thuộc Điểm loại trừ (phẫu thuật thẩm mỹ tự chọn, điều trị cận thị, thực phẩm chức năng).\n"
            "4. Hồ sơ nộp quá thời hạn 60 ngày hoặc thiếu Hóa đơn tài chính hợp pháp.\n\n"
            "⚖️ 2. Quy trình khiếu nại & Tái thẩm định:\n"
            "Nếu Quý khách cho rằng quyết định từ chối chưa thỏa đáng, Quý khách có quyền nộp 'Đơn đề nghị tái thẩm định' kèm theo giải trình y khoa bổ sung từ bác sĩ điều trị trong vòng 30 ngày. Hội đồng Giám định cấp cao sẽ xem xét lại độc lập.\n\n"
            "💡 Lời khuyên chuyên gia: Hãy kiểm tra kỹ lý do từ chối trên thông báo bồi thường trước khi gửi hồ sơ bổ sung!"
        )
        suggests = [
            "Điểm loại trừ bảo hiểm gồm những gì?",
            "Hồ sơ bồi thường cần giấy tờ gì?",
            "Thời gian chờ bệnh hiểm nghèo?",
            "Liên hệ Giám định viên hỗ trợ?"
        ]
        return reply, suggests

    # 15. Hủy hợp đồng, Rút tiền & Giá trị hoàn lại
    if any(k in q for k in ["hủy", "huy", "rút tiền", "rut tien", "trả lại tiền", "tra lai tien", "lấy lại tiền", "lay lai tien", "hoàn tiền", "hoan tien", "21 ngày", "21 ngay", "chấm dứt"]):
        reply = (
            "Kính chào Quý khách! Về quy tắc Hủy Hợp Đồng và Hoàn Trả Phí Bảo Hiểm:\n\n"
            "⏱️ 1. Thời gian 21 ngày cân nhắc (Free-look Period):\n"
            "Kể từ ngày nhận bàn giao hợp đồng, Quý khách có 21 NGÀY để đọc kỹ điều khoản. Nếu quyết định không tham gia, Quý khách được quyền hủy hợp đồng và nhận lại 100% PHÍ BẢO HIỂM ĐÃ ĐÓNG (chỉ trừ chi phí khám sức khỏe nếu có).\n\n"
            "📉 2. Hủy hợp đồng sau 21 ngày:\n"
            "Các sản phẩm bảo hiểm sức khỏe và tai nạn của InsurTech là bảo hiểm phi nhân thọ thuần bảo vệ (không tích lũy tiết kiệm sinh lời). Khi hủy hợp đồng giữa kỳ, phí chỉ được hoàn lại theo tỷ lệ thời gian chưa sử dụng nếu chưa từng phát sinh bất kỳ yêu cầu bồi thường nào.\n\n"
            "💡 Lời khuyên chuyên gia: Hãy cân nhắc duy trì hợp đồng liên tục để bảo vệ nguồn tài chính trước rủi ro bất ngờ!"
        )
        suggests = [
            "Thời gian ân hạn đóng phí?",
            "Quyền lợi bảo hiểm sức khỏe gồm gì?",
            "Tư vấn gói bảo hiểm tuổi 32?",
            "Xem lịch sử đóng phí định kỳ?"
        ]
        return reply, suggests

    # 16. Nộp phí định kỳ, Quá hạn & Thời gian ân hạn 30 ngày
    if any(k in q for k in ["đóng phí", "dong phi", "nộp tiền", "nop tien", "quá hạn", "qua han", "trễ hạn", "tre han", "ân hạn", "an han", "hết hạn", "het han", "quên đóng", "quen dong"]):
        reply = (
            "Kính chào Quý khách! Về quy tắc nộp phí bảo hiểm và Thời Gian Ân Hạn 30 Ngày:\n\n"
            "🛡️ 1. Cơ chế ân hạn bảo vệ quyền lợi:\n"
            "• InsurTech áp dụng thời gian ân hạn 30 NGÀY kể từ ngày đến hạn nộp phí định kỳ.\n"
            "• Trong suốt 30 ngày này, hợp đồng của bạn VẪN DUY TRÌ HIỆU LỰC BẢO VỆ 100%. Nếu không may có rủi ro xảy ra, công ty vẫn chi trả bồi thường đầy đủ (và cấn trừ kỳ phí còn thiếu).\n\n"
            "⚠️ 2. Sau 30 ngày nếu chưa hoàn tất đóng phí:\n"
            "• Hợp đồng sẽ tạm thời mất hiệu lực. Mọi sự kiện phát sinh sau thời điểm này sẽ không được bồi thường.\n"
            "• Quý khách có thời hạn 2 NĂM để làm thủ tục khôi phục hiệu lực hợp đồng bằng cách đóng bù phí và xác nhận sức khỏe hiện tại.\n\n"
            "💡 Lời khuyên chuyên gia: Quý khách hãy vào tab 'Thu Phí Định Kỳ' trên menu để kiểm tra hạn nộp và thanh toán trực tuyến nhanh chóng!"
        )
        suggests = [
            "Xem nhật ký thu phí định kỳ?",
            "Thủ tục cấp hợp đồng mới?",
            "Hạn mức bảo hiểm của tôi?",
            "Tư vấn gói bảo hiểm phù hợp?"
        ]
        return reply, suggests

    # 17. Khám Nha khoa & Răng miệng (Dental Care)
    if any(k in q for k in ["nha khoa", "răng", "rang", "nhổ răng", "nho rang", "răng khôn", "rang khon", "chữa tủy", "chua tuy", "trám răng", "tram rang", "sâu răng", "sau rang", "bọc sứ", "boc su", "niềng răng", "nieng rang", "lấy cao răng", "lay cao rang"]):
        reply = (
            "Kính chào Quý khách! Về quyền lợi chăm sóc Nha Khoa & Răng Miệng:\n\n"
            "🦷 1. Các chi phí nha khoa ĐƯỢC BỒI THƯỜNG (Bệnh lý bắt buộc):\n"
            "• Nhổ răng khôn mọc lệch, mọc ngầm có chỉ định phẫu thuật của bác sĩ chuyên khoa.\n"
            "• Điều trị tủy răng viêm cấp tính, áp xe quanh cuống răng.\n"
            "• Trám răng sâu bệnh lý, hàn răng do chấn thương tai nạn.\n\n"
            "❌ 2. Các chi phí nha khoa BỊ LOẠI TRỪ (Thẩm mỹ & Tự chọn):\n"
            "• Lấy cao răng định kỳ, tẩy trắng răng.\n"
            "• Niềng răng chỉnh nha, bọc răng sứ thẩm mỹ, dán sứ Veneer.\n"
            "• Cấy ghép Implant thẩm mỹ tự chọn không do di chứng tai nạn.\n\n"
            "💡 Lời khuyên chuyên gia: Khi điều trị răng bệnh lý, Quý khách cần lấy Phiếu chỉ định điều trị và Hóa đơn chi tiết dịch vụ nha khoa để gửi thẩm định bồi thường!"
        )
        suggests = [
            "Phẫu thuật thẩm mỹ có được chi trả?",
            "Khám mắt có được thanh toán không?",
            "Hồ sơ bồi thường cần giấy tờ gì?",
            "Hạn mức viện phí phẫu thuật?"
        ]
        return reply, suggests

    # 18. Khám Mắt & Tật khúc xạ (Eye Care & Vision)
    if any(k in q for k in ["mắt", "mat", "cận thị", "can thi", "loạn thị", "mổ lasik", "lasik", "đục thủy tinh thể", "duc thuy tinh the", "cườm khô", "phaco"]):
        reply = (
            "Kính chào Quý khách! Về quyền lợi điều trị bệnh lý về Mắt:\n\n"
            "👁️ 1. Các phẫu thuật mắt ĐƯỢC THANH TOÁN (Bệnh lý):\n"
            "• Phẫu thuật mổ đục thủy tinh thể (Phaco) thay thủy tinh thể nhân tạo sau thời gian chờ bệnh đặc biệt.\n"
            "• Phẫu thuật bong võng mạc, mộng thịt độ nặng, glôcôm (tăng nhãn áp).\n"
            "• Điều trị chấn thương mắt do tai nạn phát sinh.\n\n"
            "❌ 2. Chi phí BỊ LOẠI TRỪ:\n"
            "• Phẫu thuật điều trị tật khúc xạ mắt (mổ cận thị Lasik, Femto, ReLEx SMILE).\n"
            "• Chi phí đo khám khúc xạ và mua kính mắt, kính áp tròng.\n\n"
            "💡 Lời khuyên chuyên gia: Các phẫu thuật bệnh lý mắt đều được thanh toán theo hạn mức phẫu thuật nội trú của gói bảo hiểm sức khỏe!"
        )
        suggests = [
            "Điểm loại trừ bảo hiểm gồm những gì?",
            "Thời gian chờ phẫu thuật bao lâu?",
            "Hồ sơ bồi thường cần chứng từ gì?",
            "Nha khoa có được chi trả không?"
        ]
        return reply, suggests

    # 19. Mua nhiều hợp đồng bảo hiểm cùng lúc (Trùng bảo hiểm)
    if any(k in q for k in ["nhiều bảo hiểm", "nhieu bao hiem", "trùng", "trung", "2 bảo hiểm", "2 thẻ", "công ty khác", "bảo hiểm y tế", "bhyt", "thanh toán kép", "đền bù gấp đôi"]):
        reply = (
            "Kính chào Quý khách! Về nguyên tắc khi sở hữu Nhiều Hợp Đồng Bảo Hiểm hoặc có thêm BHYT Nhà nước:\n\n"
            "⚖️ 1. Đối với chi phí Viện phí khám chữa bệnh (Nguyên tắc Bồi hoàn thực tế):\n"
            "• Quý khách không được thanh toán vượt quá số tiền thực tế ghi trên hóa đơn bệnh viện.\n"
            "• Tuy nhiên, nếu BHYT Nhà nước hoặc một công ty bảo hiểm khác đã chi trả một phần, InsurTech sẽ tiếp tục thanh toán phần chi phí chênh lệch còn lại mà Quý khách phải bỏ tiền túi!\n\n"
            "💰 2. Đối với Bệnh Hiểm Nghèo & Tai Nạn (Nguyên tắc Khoán tiền mặt):\n"
            "• ĐƯỢC HƯỞNG ĐỘC LẬP TỪ TẤT CẢ CÁC HỢP ĐỒNG! Nếu Quý khách có 2 gói bệnh hiểm nghèo tại 2 công ty khác nhau, cả 2 nơi đều sẽ chi trả 100% tiền mặt theo mệnh giá cam kết.\n\n"
            "💡 Lời khuyên chuyên gia: Kết hợp song song BHYT Nhà nước và Bảo hiểm InsurTech là giải pháp tối ưu giúp Quý khách gần như không phải chi trả thêm bất kỳ viện phí nào!"
        )
        suggests = [
            "Gói bệnh hiểm nghèo hạn mức bao nhiêu?",
            "Bảo hiểm tai nạn chi trả thế nào?",
            "Hồ sơ claim bồi thường cần gì?",
            "Thẻ bảo lãnh viện phí dùng ở đâu?"
        ]
        return reply, suggests

    # 20. Điểm loại trừ bồi thường tổng quát
    if any(k in q for k in ["loại trừ", "loai tru", "không được", "khong duoc", "không chi trả", "khong chi tra", "điểm loại trừ", "diem loai tru"]):
        reply = (
            "Kính chào Quý khách! Dưới đây là Bảng Tổng Hợp Các Điểm Loại Trừ Không Được Chi Trả theo Quy tắc bảo hiểm:\n\n"
            "🚫 1. Bệnh có sẵn và tiền sử bệnh lý không kê khai trung thực khi tham gia.\n"
            "🚫 2. Hành vi vi phạm pháp luật, sử dụng rượu bia vượt nồng độ cồn cho phép khi lái xe, hoặc sử dụng chất gây nghiện.\n"
            "🚫 3. Phẫu thuật thẩm mỹ làm đẹp tự nguyện, nha khoa thẩm mỹ (niềng răng, bọc sứ), điều trị cận thị tật khúc xạ mắt.\n"
            "🚫 4. Khám sức khỏe tổng quát định kỳ, kiểm tra vô sinh, điều trị hiếm muộn, kế hoạch hóa gia đình.\n"
            "🚫 5. Bệnh phát sinh trong Thời gian chờ (30 ngày với bệnh thường, 90 ngày với bệnh hiểm nghèo, 270 ngày với thai sản).\n"
            "🚫 6. Thực phẩm chức năng, thuốc bổ, khoáng chất không thuộc danh mục thuốc kê đơn điều trị bệnh của Bộ Y tế.\n\n"
            "💡 Tất cả các trường hợp bệnh tật và tai nạn hợp pháp ngoài các điểm trên đều được thanh toán tối đa theo hạn mức hợp đồng!"
        )
        suggests = [
            "Phẫu thuật thẩm mỹ có ngoại lệ không?",
            "Thời gian chờ bệnh hiểm nghèo?",
            "Hạn mức viện phí phẫu thuật?",
            "Bệnh có sẵn được chi trả không?"
        ]
        return reply, suggests

    # 21. Công nghệ AI Copilot & Cơ chế kiểm soát an toàn
    if any(k in q for k in ["ai", "copilot", "trí tuệ nhân tạo", "tri tue nhan tao", "bảo mật", "bao mat", "pii", "thẩm định tự động", "an toàn"]):
        reply = (
            "Kính chào Quý khách! Tôi là Trợ lý Ảo InsurTech Smart Advisor, vận hành trên nền tảng AI Copilot thế hệ mới với 3 cơ chế kiểm soát an toàn:\n\n"
            "🛡️ 1. Khử định danh dữ liệu y tế (PII Masking):\n"
            "Tự động làm mờ số CCCD, mã số thẻ y tế, số điện thoại trước khi đưa vào phân tích nhằm bảo vệ tuyệt đối quyền riêng tư khách hàng.\n\n"
            "⚡ 2. Thẩm định bồi thường tự động trong 30 giây:\n"
            "Phân tích chẩn đoán y khoa, đối soát từng dòng hóa đơn viện phí với bảng quyền lợi và rà soát dấu hiệu gian lận bất thường.\n\n"
            "🤝 3. Cơ chế Giám sát con người (Human-in-the-Loop):\n"
            "AI chỉ đóng vai trò Trợ lý đưa ra khuyến nghị kỹ thuật dự thảo. Giám định viên con người luôn là người kiểm duyệt cuối cùng và trực tiếp ký duyệt quyết định chi trả bồi thường.\n\n"
            "Quý khách có thể đặt bất kỳ câu hỏi nào về quy tắc, quyền lợi và thủ tục bồi thường để tôi hỗ trợ ngay!"
        )
        suggests = [
            "Phẫu thuật thẩm mỹ có được chi trả?",
            "Thời gian chờ bệnh hiểm nghèo?",
            "Hồ sơ bồi thường cần giấy tờ gì?",
            "Gói bảo hiểm sức khỏe tối ưu?"
        ]
        return reply, suggests

    # 22. Lời chào & Giới thiệu chuyên gia
    if any(k in q for k in ["xin chào", "xin chao", "chào", "chao", "hello", "hi", "bạn là ai", "ai đó", "giúp gì", "tư vấn gì"]):
        reply = (
            "Kính chào Quý khách! Tôi là **Trợ lý Ảo InsurTech Smart Advisor (AI Copilot)** - Chuyên gia Tư vấn Nghiệp vụ Bảo hiểm Thông minh 24/7.\n\n"
            "Tôi có thể hỗ trợ Quý khách giải đáp chuẩn xác và tức thì các vấn đề sau:\n"
            "• 🏥 Tra cứu quyền lợi nằm viện, hạn mức phẫu thuật và tiền giường phòng dịch vụ.\n"
            "• ⏳ Kiểm tra thời gian chờ chi tiết cho từng nhóm bệnh và các điểm loại trừ.\n"
            "• 📋 Hướng dẫn chuẩn bị chứng từ và nộp hồ sơ yêu cầu bồi thường (Claim) online.\n"
            "• 💡 Tư vấn lựa chọn gói bảo hiểm tối ưu theo độ tuổi, nghề nghiệp và ngân sách.\n"
            "• 💳 Hướng dẫn sử dụng thẻ bảo lãnh viện phí, thời gian ân hạn nộp phí và khôi phục hợp đồng.\n\n"
            "Quý khách đang quan tâm đến gói bảo hiểm nào hoặc cần tư vấn điều khoản gì hôm nay?"
        )
        suggests = [
            "Phẫu thuật thẩm mỹ có được chi trả?",
            "Thời gian chờ bệnh hiểm nghèo?",
            "Gợi ý gói bảo hiểm tuổi 32?",
            "Hồ sơ claim bồi thường cần gì?",
            "Gãy xương do tai nạn bồi thường thế nào?",
            "Hạn mức viện phí & phẫu thuật nội trú?"
        ]
        return reply, suggests

    # 23. Cảm ơn, Khen ngợi & Phản hồi tích cực
    if any(k in q for k in ["cảm ơn", "cam on", "cám ơn", "thank", "tuyệt vời", "tuyet voi", "tốt quá", "tot qua", "hay quá", "hay qua", "rõ ràng rồi", "hiểu rồi", "ok"]):
        reply = (
            "Dạ, InsurTech AI rất vinh hạnh được hỗ trợ Quý khách! Chúc Quý khách và gia đình luôn dồi dào sức khỏe, an tâm và hạnh phúc.\n\n"
            "Nếu Quý khách có thêm bất kỳ câu hỏi nào về điều khoản, thủ tục hoặc khi phát sinh sự kiện y tế, đừng ngần ngại gửi tin nhắn để tôi hỗ trợ ngay nhé!"
        )
        suggests = [
            "Nộp hồ sơ bồi thường online?",
            "Danh mục các gói sản phẩm bảo hiểm?",
            "Tra cứu hợp đồng bảo hiểm hiện tại?",
            "Kiểm tra lịch sử đóng phí định kỳ?"
        ]
        return reply, suggests

    # 24. Phản hồi Ngữ cảnh Chuyên gia Tổng quát cho các câu hỏi tình huống khác
    reply = (
        f"Kính chào Quý khách! Cảm ơn câu hỏi của Quý khách về nội dung: '{user_query}'.\n\n"
        "Căn cứ trên Bảng Quy tắc Điều khoản hiện hành của Hệ thống Bảo hiểm InsurTech, Chuyên gia xin tư vấn như sau:\n\n"
        "🎯 1. Nguyên tắc giải quyết chung:\n"
        "• Tất cả các chi phí khám chữa bệnh nội trú hợp lý, có chỉ định y khoa của bác sĩ chuyên khoa và vượt qua Thời gian chờ quy định đều được thanh toán tối đa theo hạn mức hợp đồng.\n"
        "• Các gói bảo hiểm hiện hành gồm: Gói Sức khỏe Phúc An Toàn Diện (Hạn mức 50M), Gói Bệnh Hiểm Nghèo Vững Tâm (Hạn mức 200M), và Gói Tai Nạn Cá Nhân (Hạn mức 100M).\n\n"
        "📋 2. Các bước xử lý bồi thường:\n"
        "• Nếu Quý khách đang có hóa đơn viện phí cần thanh toán, hãy giữ lại Giấy ra viện và Hóa đơn điện tử GTGT.\n"
        "• Bấm nút 'Nộp Hồ Sơ Claim' ở góc trên bên phải để nộp online, máy chủ AI sẽ thẩm định sơ bộ trong 30 giây.\n\n"
        "💡 Lời khuyên chuyên gia: Để được tư vấn chuẩn xác nhất cho từng bệnh án cụ thể, Quý khách có thể cung cấp thêm thông tin chẩn đoán hoặc tên bệnh viện điều trị nhé!"
    )
    suggests = [
        "Phẫu thuật thẩm mỹ có được chi trả?",
        "Thời gian chờ bệnh hiểm nghèo?",
        "Gợi ý gói bảo hiểm theo độ tuổi?",
        "Hồ sơ claim bồi thường cần gì?"
    ]
    return reply, suggests

def generate_chatbot_advice(user_query: str, policy_context: str = "") -> AdvisorChatResponse:
    """Tạo phản hồi tư vấn chính sách bảo hiểm đa dạng, chuyên nghiệp và chuẩn xác."""
    from app.config import settings
    from app.services.resilient_ai_service import call_ai_chat_completion

    # 1. Thử gọi mô hình OpenAI nếu có API Key thật
    if settings.OPENAI_API_KEY and not settings.AI_MOCK_MODE:
        system_prompt = (
            "Bạn là Trợ lý Ảo Tư vấn Bảo hiểm chuyên nghiệp của Hệ thống InsurTech Smart System. "
            "Hãy giải đáp câu hỏi của khách hàng dựa trên quy tắc điều khoản bảo hiểm. "
            "Không bịa đặt thông tin, trả lời chi tiết, ân cần, chia theo các ý gạch đầu dòng rõ ràng."
        )
        user_prompt = f"Câu hỏi của khách hàng: {user_query}\nNgữ cảnh điều khoản sản phẩm: {policy_context}"
        ai_reply = call_ai_chat_completion(system_prompt, user_prompt)
        if ai_reply:
            return AdvisorChatResponse(
                reply=ai_reply,
                disclaimer="Trợ lý AI giải đáp căn cứ trên bảng điều khoản hiện hành của hệ thống InsurTech."
            )

    # 2. Sử dụng Knowledge Base đa dạng, chuyên sâu (mỗi câu hỏi trả về câu trả lời riêng biệt)
    res = generate_expert_insurance_advisor_reply(user_query, policy_context)
    if isinstance(res, tuple):
        reply_text, suggests = res
    else:
        reply_text, suggests = res, []

    return AdvisorChatResponse(
        reply=reply_text,
        disclaimer="Trợ lý AI giải đáp căn cứ trên bảng điều khoản hiện hành của hệ thống InsurTech.",
        suggested_questions=suggests
    )

def calculate_underwriting_risk(age_group: str, claim_ratio: float, job_category: str, risk_notes: str) -> RiskScoringResponse:
    """Chấm điểm rủi ro định phí hợp đồng bảo hiểm."""
    base_score = 20
    adjustment = 0.0

    if "50" in age_group or "60" in age_group:
        base_score += 25
        adjustment += 10.0
    elif "40" in age_group:
        base_score += 10
        adjustment += 5.0

    if claim_ratio > 50:
        base_score += 30
        adjustment += 15.0
    elif claim_ratio > 20:
        base_score += 15
        adjustment += 5.0

    if "lao động" in job_category.lower() or "công trường" in job_category.lower():
        base_score += 20
        adjustment += 10.0

    risk_score = min(base_score, 95)
    if risk_score < 35:
        level = "Thấp (Khách hàng tiêu chuẩn)"
        rec = "Chấp thuận bảo vệ với mức phí chuẩn thông thường."
    elif risk_score < 60:
        level = "Trung bình (Có nguy cơ phát sinh claim)"
        rec = f"Chấp thuận bảo vệ có điều kiện, đề xuất phụ phí +{adjustment:.1f}%."
    else:
        level = "Cao (Nguy cơ rủi ro cao)"
        rec = f"Cần thẩm định y khoa chuyên sâu trước khi cấp đơn, phụ phí tối thiểu +{adjustment:.1f}%."

    return RiskScoringResponse(
        risk_score=risk_score,
        risk_level=level,
        premium_adjustment_percent=adjustment,
        underwriting_notes=f"Đánh giá rủi ro nhóm tuổi {age_group}, nghề nghiệp {job_category}, tỷ lệ claim lịch sử {claim_ratio}%.",
        recommendation=rec
    )
