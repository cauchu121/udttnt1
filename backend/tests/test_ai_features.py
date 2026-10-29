import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_token(email, password):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]

def test_claim_assessment_by_officer():
    token = get_auth_token("officer@insurtech.vn", "Officer@123")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/ai/claim-assessment", json={"claim_id": 1}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_amount" in data
    assert "fraud_risk_score" in data
    assert data["recommended_amount"] <= data["max_coverage_limit"]
    assert len(data["disclaimer"]) > 0

def test_ai_assessment_forbidden_for_customer():
    token = get_auth_token("customer@insurtech.vn", "Customer@123")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/ai/claim-assessment", json={"claim_id": 1}, headers=headers)
    assert response.status_code == 403

def test_ai_chat_advisor():
    token = get_auth_token("customer@insurtech.vn", "Customer@123")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/ai/chat-advisor", json={"message": "Gói bảo hiểm sức khỏe có chi trả phẫu thuật không?"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "disclaimer" in data
