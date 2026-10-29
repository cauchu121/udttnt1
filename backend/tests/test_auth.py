import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@insurtech.vn",
        "password": "Admin@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@insurtech.vn"
    assert data["user"]["role"] == "admin"

def test_login_wrong_password():
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@insurtech.vn",
        "password": "WrongPassword999"
    })
    assert response.status_code == 401

def test_register_duplicate_email():
    response = client.post("/api/v1/auth/register", json={
        "email": "admin@insurtech.vn",
        "password": "NewPassword123",
        "full_name": "Nguyen Van A"
    })
    assert response.status_code == 400
