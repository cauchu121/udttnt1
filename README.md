# Hệ Thống Quản Lý Bảo Hiểm Có Tích Hợp AI (InsurTech Smart System)

**Báo cáo môn:** Ứng dụng Trí tuệ Nhân tạo  
**Trường Đại học Công nghệ Thông tin và Truyền thông - Khoa Công nghệ Thông tin**  
**Giảng viên hướng dẫn:** Nguyễn Tuấn Anh  
**Sinh viên thực hiện:**
- Nguyễn Minh Quang (KTPM K23C)
- Lê Đắc Lộc (KTPM K23C)

---

## 1. Giới thiệu Dự án
Hệ thống InsurTech Smart System là nền tảng quản lý bảo hiểm thế hệ mới, tích hợp Trí tuệ Nhân tạo Tạo sinh (Generative AI) để giải quyết các điểm nghẽn nghiệp vụ cốt lõi:
- **Thẩm định hồ sơ bồi thường tự động (AI Claim Assessment & Fraud Detection):** Phân tích chẩn đoán, đối soát chi phí hóa đơn y tế với bảng quyền lợi hợp đồng và phát hiện các dấu hiệu gian lận bất thường.
- **Quy trình Human-in-the-loop:** Kết quả do AI sinh ra đóng vai trò dự thảo (Draft) trên Modal Preview, Giám định viên có quyền điều chỉnh số tiền duyệt trước khi lưu quyết định chính thức vào CSDL.
- **Trợ lý ảo AI Advisor Chatbot:** Tư vấn quyền lợi sản phẩm, giải đáp quy tắc điều khoản loại trừ 24/7.
- **Bảo mật PII & Resilience:** Cơ chế ẩn danh dữ liệu y tế (PII Masking), Timeout 15s, Exponential Backoff cho lỗi Rate Limit (429) và Fallback Mode an toàn.

---

## 2. Thông tin Tài khoản Thử nghiệm (Demo Accounts)

| Vai trò | Email | Mật khẩu | Quyền hạn chính |
| :--- | :--- | :--- | :--- |
| **Giám định viên (Claims Officer)** | `officer@insurtech.vn` | `Officer@123` | Thẩm định hồ sơ claim, kích hoạt AI Copilot, duyệt chi trả |
| **Quản trị viên (Admin)** | `admin@insurtech.vn` | `Admin@123` | Quản lý toàn bộ gói bảo hiểm, hợp đồng và người dùng |
| **Đại lý bảo hiểm (Agent)** | `agent@insurtech.vn` | `Agent@123` | Tư vấn khách hàng, phát hành hợp đồng mới |
| **Khách hàng (Customer)** | `customer@insurtech.vn` | `Customer@123` | Tra cứu hợp đồng, nộp hồ sơ yêu cầu bồi thường |

---

## 3. Hướng dẫn Khởi chạy Hệ thống

### Cách 1: Khởi chạy 1-Click trên Windows
Nhấp đúp chuột vào file:
```bat
run_all.bat
```
Hệ thống sẽ tự động khởi tạo CSDL SQLite, nạp dữ liệu mẫu và bật Backend Server trên cổng `8000`.

### Cách 2: Khởi chạy bằng dòng lệnh
```bash
# 1. Cài đặt các thư viện phụ thuộc
pip install -r backend/requirements.txt

# 2. Khởi tạo và nạp dữ liệu mẫu
python backend/seed_data.py

# 3. Khởi chạy FastAPI server
set PYTHONPATH=backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 4. Truy cập Ứng dụng
- **Giao diện Web Portal:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Tài liệu Tương tác Swagger API (Docs):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Kiểm tra Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 5. Chạy Kiểm thử Tự động (Pytest)
```bash
set PYTHONPATH=backend
python -m pytest backend/tests -v
```
Toàn bộ 8 ca kiểm thử (Auth, Claims, AI Resilience, Security RBAC, Boundary) đã được cấu hình và kiểm chứng thành công 100%.
