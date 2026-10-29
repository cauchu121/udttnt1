import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_make_payment_with_receipt():
    # 1. Đăng nhập với tài khoản khách hàng
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "customer@insurtech.vn",
        "password": "Customer@123"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Lấy danh sách hợp đồng
    policies_resp = client.get("/api/v1/policies", headers=headers)
    assert policies_resp.status_code == 200
    policies = policies_resp.json()
    assert len(policies) > 0
    policy_id = policies[0]["id"]

    # 3. Gửi đóng phí có đính kèm ảnh biên lai
    fake_receipt_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    pay_resp = client.post("/api/v1/finance/payments", json={
        "policy_id": policy_id,
        "period_name": "Kỳ Thường Niên Năm 2026",
        "amount": 3500000.0,
        "payment_method": "BANK_TRANSFER",
        "receipt_image": fake_receipt_base64
    }, headers=headers)
    assert pay_resp.status_code == 201
    pay_data = pay_resp.json()
    assert pay_data["amount"] == 3500000.0
    assert pay_data["receipt_image"] == fake_receipt_base64
    assert pay_data["status"] == "PAID"

    # 4. Kiểm tra danh sách thanh toán có chứa giao dịch và ảnh biên lai
    list_resp = client.get("/api/v1/finance/payments", headers=headers)
    assert list_resp.status_code == 200
    payments = list_resp.json()
    assert any(p["payment_code"] == pay_data["payment_code"] and p["receipt_image"] == fake_receipt_base64 for p in payments)
