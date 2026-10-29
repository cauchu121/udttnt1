import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import datetime
from app.database import engine, SessionLocal, Base
from app.models import User, InsuranceProduct, InsurancePolicy, Claim, ClaimDocument, PremiumPayment
from app.auth import hash_password

def seed_database():
    print("Khởi tạo cấu trúc bảng CSDL...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Kiểm tra nếu đã có dữ liệu thì không tạo trùng
        if db.query(User).filter(User.email == "admin@insurtech.vn").first():
            print("Cơ sở dữ liệu đã có dữ liệu mẫu. Bỏ qua seed.")
            return

        print("Đang nạp 4 tài khoản người dùng mẫu...")
        admin = User(
            email="admin@insurtech.vn",
            hashed_password=hash_password("Admin@123"),
            full_name="Nguyễn Văn Quản Trị",
            phone="0912345678",
            identity_card="001099012345",
            role="admin",
            is_active=True
        )
        officer = User(
            email="officer@insurtech.vn",
            hashed_password=hash_password("Officer@123"),
            full_name="Trần Thị Giám Định",
            phone="0987654321",
            identity_card="001099054321",
            role="claims_officer",
            is_active=True
        )
        agent = User(
            email="agent@insurtech.vn",
            hashed_password=hash_password("Agent@123"),
            full_name="Lê Hoàng Đại Lý",
            phone="0905123456",
            identity_card="001099078901",
            role="agent",
            is_active=True
        )
        customer = User(
            email="customer@insurtech.vn",
            hashed_password=hash_password("Customer@123"),
            full_name="Nguyễn Minh Quang",
            phone="0934567890",
            identity_card="001099099887",
            role="customer",
            is_active=True
        )

        db.add_all([admin, officer, agent, customer])
        db.commit()
        db.refresh(customer)

        print("Đang nạp 3 gói sản phẩm bảo hiểm chuẩn...")
        prd_health = InsuranceProduct(
            product_code="PRD-HLT-01",
            product_name="Bảo hiểm Sức khỏe Phúc An Toàn diện",
            category="Sức khỏe",
            description="Bảo vệ toàn diện trước rủi ro ốm đau, bệnh tật, phẫu thuật nội trú và nằm viện điều trị chuyên khoa.",
            max_coverage_limit=50000000.0,
            base_annual_premium=3500000.0,
            terms_and_conditions="""【1. QUYỀN LỢI CHI TRẢ NỘI TRÚ】
- Chi phí giường bệnh & phòng nằm viện: Tối đa 1.500.000 VNĐ/ngày (tối đa 60 ngày/năm).
- Chi phí phẫu thuật điều trị nội trú: Chi trả 100% chi phí thực tế theo hóa đơn, tối đa 30.000.000 VNĐ/ca phẫu thuật.
- Phòng chăm sóc đặc biệt (ICU): Tối đa 3.000.000 VNĐ/ngày (tối đa 30 ngày/năm).
- Thuốc men, vật tư tiêu hao, xét nghiệm, chẩn đoán hình ảnh nội trú: Thanh toán theo chi phí thực tế hợp lý.

【2. THỜI GIAN CHỜ HIỆU LỰC】
- Tai nạn: 0 ngày (bảo vệ tức thì ngay sau giờ ký kết).
- Bệnh thông thường (ốm sốt, phẫu thuật ruột thừa, viêm phế quản): 30 ngày.
- Bệnh hô hấp, tai mũi họng, tiểu phẫu mạn tính: 180 ngày.
- Bệnh đặc biệt, bệnh có sẵn được chấp thuận, thai sản: 365 ngày (1 năm).

【3. ĐIỂM LOẠI TRỪ TRÁCH NHIỆM BẢO HIỂM】
- Phẫu thuật thẩm mỹ, tạo hình thẩm mỹ (nâng mũi, hút mỡ, độn cằm, cắt mí), nha khoa thẩm mỹ không do tai nạn.
- Bệnh có sẵn hoặc tiền sử bệnh lý không kê khai trung thực trên Giấy yêu cầu bảo hiểm.
- Kiểm tra sức khỏe định kỳ, tầm soát bệnh lý không có chỉ định điều trị của bác sĩ chuyên khoa.
- Tự tử, cố ý tự gây thương tích, sử dụng chất kích thích/ma túy, vi phạm nồng độ cồn khi tham gia giao thông.

【4. CHỨNG TỪ BỒI THƯỜNG YÊU CẦU】
- Giấy ra viện có dấu mộc bệnh viện; Bảng kê chi tiết viện phí (Mẫu 01/BV).
- Hóa đơn tài chính hợp pháp (Hóa đơn điện tử có mã cơ quan thuế).
- Giấy chứng nhận phẫu thuật / Toa thuốc xuất viện.""",
            is_active=True
        )
        prd_accident = InsuranceProduct(
            product_code="PRD-ACC-02",
            product_name="Bảo hiểm Tai nạn Cá nhân Toàn diện",
            category="Tai nạn",
            description="Chi trả bồi thường tổn thất thương tật và viện phí điều trị do tai nạn sinh hoạt, giao thông 24/7.",
            max_coverage_limit=100000000.0,
            base_annual_premium=2000000.0,
            terms_and_conditions="""【1. QUYỀN LỢI TAI NẠN CÁ NHÂN 24/7】
- Tử vong hoặc Thương tật toàn bộ vĩnh viễn do tai nạn: Chi trả 100% hạn mức (100.000.000 VNĐ).
- Thương tật bộ phận vĩnh viễn: Chi trả theo Bảng tỷ lệ thương tật chuẩn Bộ Tài Chính (ví dụ: gãy xương 15-25%, mất ngón 10-20%).
- Chi phí y tế cấp cứu và điều trị vết thương do tai nạn: Chi trả thực tế tối đa 20.000.000 VNĐ/vụ.
- Trợ cấp thu nhập nằm viện điều trị tai nạn: 150.000 VNĐ/ngày (tối đa 90 ngày/năm).

【2. THỜI GIAN CHỜ HIỆU LỰC】
- 0 ngày: Toàn bộ rủi ro tai nạn giao thông, sinh hoạt, lao động được bảo vệ ngay khi hợp đồng có hiệu lực.

【3. ĐIỂM LOẠI TRỪ TRÁCH NHIỆM BẢO HIỂM】
- Vi phạm luật an toàn giao thông với nồng độ cồn trong máu/hơi thở vượt ngưỡng cho phép; sử dụng chất ma túy.
- Tham gia các môn thể thao mạo hiểm (đua xe, leo núi chuyên nghiệp, lặn biển bình dưỡng khí, nhảy dù) không mua gói mở rộng.
- Hành vi cố ý vi phạm pháp luật hình sự, chống người thi hành công vụ.
- Đột quỵ, tai biến mạch máu não, nhồi máu cơ tim (bệnh lý nội khoa không thuộc định nghĩa tai nạn ngoại lực).

【4. CHỨNG TỪ BỒI THƯỜNG YÊU CẦU】
- Biên bản khám nghiệm hiện trường/kết luận của cơ quan Công an (tai nạn giao thông) hoặc Biên bản xác nhận tai nạn sinh hoạt.
- Giấy chứng nhận thương tích, Bệnh án cấp cứu ban đầu.
- Hóa đơn điện tử, bảng kê chi phí phẫu thuật cố định xương, phim X-quang/CT.""",
            is_active=True
        )
        prd_surgery = InsuranceProduct(
            product_code="PRD-MED-03",
            product_name="Bảo hiểm Bệnh hiểm nghèo & Viện phí Nâng cao",
            category="Bệnh hiểm nghèo",
            description="Hỗ trợ tài chính tức thì lên đến 200 triệu đồng khi phát hiện bệnh hiểm nghèo giai đoạn đầu.",
            max_coverage_limit=200000000.0,
            base_annual_premium=6500000.0,
            terms_and_conditions="""【1. QUYỀN LỢI BỆNH HIỂM NGHÈO & VIỆN PHÍ NÂNG CAO】
- Bệnh hiểm nghèo giai đoạn đầu: Chi trả trước 25% hạn mức (50.000.000 VNĐ) để người bệnh kịp thời điều trị.
- Bệnh hiểm nghèo giai đoạn sau: Chi trả 100% hạn mức (200.000.000 VNĐ) cho 45 danh mục bệnh hiểm nghèo chuẩn Bộ Y Tế.
- Trợ cấp tài chính hồi phục đại phẫu bệnh lý: 10.000.000 VNĐ sau phẫu thuật.
- Miễn đóng toàn bộ phí bảo hiểm định kỳ còn lại của hợp đồng khi mắc bệnh hiểm nghèo giai đoạn sau.

【2. THỜI GIAN CHỜ HIỆU LỰC】
- Thời gian chờ tiêu chuẩn: 90 ngày kể từ ngày hợp đồng có hiệu lực.
- Điều kiện sống sót: Người được bảo hiểm sống tối thiểu 14 ngày kể từ ngày có kết luận chẩn đoán xác định.

【3. ĐIỂM LOẠI TRỪ TRÁCH NHIỆM BẢO HIỂM】
- Bệnh hiểm nghèo khởi phát, xuất hiện triệu chứng hoặc được chẩn đoán trong vòng 90 ngày thời gian chờ.
- Bệnh bẩm sinh, khiếm khuyết di truyền hoặc bệnh lý có sẵn chưa kê khai trước khi tham gia bảo hiểm.
- Nhiễm HIV/AIDS (trừ trường hợp lây nhiễm do truyền máu nghề nghiệp hoặc bị tấn công khi đang thi hành công vụ).
- Tự đầu độc, lạm dụng dược phẩm/thuốc gây nghiện không theo chỉ định y khoa.

【4. CHỨNG TỪ BỒI THƯỜNG YÊU CẦU】
- Báo cáo kết quả giải phẫu bệnh học (sinh thiết mô tế bào học) xác định ung thư/u ác tính có ký tên bác sĩ giải phẫu bệnh.
- Giấy ra viện và Tóm tắt hồ sơ bệnh án từ Bệnh viện chuyên khoa cấp tỉnh/trung ương trở lên.
- Các kết quả chẩn đoán cận lâm sàng: MRI, CT-Scanner, Siêu âm tim, Điện tâm đồ, Đo chức năng tủy.""",
            is_active=True
        )

        db.add_all([prd_health, prd_accident, prd_surgery])
        db.commit()
        db.refresh(prd_health)
        db.refresh(prd_accident)

        print("Đang nạp 2 hợp đồng bảo hiểm mẫu...")
        now = datetime.datetime.utcnow()
        policy1 = InsurancePolicy(
            policy_number="POL-2026-HLT-001",
            customer_id=customer.id,
            product_id=prd_health.id,
            start_date=now - datetime.timedelta(days=60),
            end_date=now + datetime.timedelta(days=305),
            total_sum_insured=prd_health.max_coverage_limit,
            premium_amount=prd_health.base_annual_premium,
            payment_cycle="ANNUALLY",
            status="ACTIVE"
        )
        policy2 = InsurancePolicy(
            policy_number="POL-2026-ACC-002",
            customer_id=customer.id,
            product_id=prd_accident.id,
            start_date=now - datetime.timedelta(days=30),
            end_date=now + datetime.timedelta(days=335),
            total_sum_insured=prd_accident.max_coverage_limit,
            premium_amount=prd_accident.base_annual_premium,
            payment_cycle="ANNUALLY",
            status="ACTIVE"
        )

        db.add_all([policy1, policy2])
        db.commit()
        db.refresh(policy1)
        db.refresh(policy2)

        print("Đang nạp giao dịch thu phí định kỳ...")
        payment1 = PremiumPayment(
            payment_code="PAY-202608-001",
            policy_id=policy1.id,
            period_name="Kỳ phí Năm 2026",
            amount=policy1.premium_amount,
            payment_method="BANK_TRANSFER",
            status="PAID"
        )
        payment2 = PremiumPayment(
            payment_code="PAY-202608-002",
            policy_id=policy2.id,
            period_name="Kỳ phí Năm 2026",
            amount=policy2.premium_amount,
            payment_method="MOMO",
            status="PAID"
        )
        db.add_all([payment1, payment2])
        db.commit()

        print("Đang nạp 2 hồ sơ yêu cầu bồi thường mẫu chờ thẩm định AI...")
        claim1 = Claim(
            claim_number="CLM-2026-0001",
            policy_id=policy1.id,
            customer_id=customer.id,
            incident_date=now - datetime.timedelta(days=5),
            claimed_amount=12500000.0,
            approved_amount=0.0,
            diagnosis="Phẫu thuật nội soi viêm ruột thừa cấp điều trị nội trú",
            hospital_name="Bệnh viện Đại học Y Dược",
            status="PENDING",
            fraud_risk_score=0
        )
        db.add(claim1)
        db.commit()
        db.refresh(claim1)

        doc1 = ClaimDocument(
            claim_id=claim1.id,
            document_type="Giấy chứng nhận phẫu thuật & Giấy ra viện",
            file_path="uploads/claims/giay_ra_vien_01.pdf",
            invoice_amount=0.0,
            notes="Chứng từ y tế xác nhận chẩn đoán nội khoa"
        )
        doc2 = ClaimDocument(
            claim_id=claim1.id,
            document_type="Hóa đơn GTGT viện phí nội trú & Bảng kê chi phí giường bệnh",
            file_path="uploads/claims/hoa_don_vien_phi_01.jpg",
            invoice_amount=12500000.0,
            notes="Đã thanh toán trực tiếp tại viện"
        )
        db.add_all([doc1, doc2])

        claim2 = Claim(
            claim_number="CLM-2026-0002",
            policy_id=policy2.id,
            customer_id=customer.id,
            incident_date=now - datetime.timedelta(days=2),
            claimed_amount=8200000.0,
            approved_amount=0.0,
            diagnosis="Gãy kín xương cẳng tay trái do trượt chân ngã tại nhà",
            hospital_name="Bệnh viện Chấn thương Chỉnh hình",
            status="PENDING",
            fraud_risk_score=0
        )
        db.add(claim2)
        db.commit()
        db.refresh(claim2)

        doc3 = ClaimDocument(
            claim_id=claim2.id,
            document_type="Phiếu kết quả X-Quang & Bệnh án chấn thương",
            file_path="uploads/claims/phieu_xquang_02.pdf",
            invoice_amount=0.0,
            notes="Xác nhận gãy xương cẳng tay"
        )
        doc4 = ClaimDocument(
            claim_id=claim2.id,
            document_type="Hóa đơn nẹp cố định & thuốc men điều trị ngoại trú",
            file_path="uploads/claims/hoa_don_thuoc_02.jpg",
            invoice_amount=8200000.0,
            notes="Hóa đơn điện tử có mã tra cứu"
        )
        db.add_all([doc3, doc4])
        db.commit()

        print("Khởi tạo và nạp dữ liệu mẫu hoàn tất 100%!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
