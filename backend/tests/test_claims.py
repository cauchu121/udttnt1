import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_token(email, password):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]

def test_customer_list_claims():
    token = get_auth_token("customer@insurtech.vn", "Customer@123")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/claims", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_claim_invalid_amount():
    token = get_auth_token("customer@insurtech.vn", "Customer@123")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "policy_id": 1,
        "incident_date": "2026-08-10T08:00:00",
        "claimed_amount": -5000000,
        "diagnosis": "Đau dạ dày cấp"
    }
    response = client.post("/api/v1/claims", json=payload, headers=headers)
    assert response.status_code == 422
