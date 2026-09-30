import pytest
from app.models.user import UserRole


def test_get_auth_config(client):
    res = client.get("/api/auth/config")
    assert res.status_code == 200
    data = res.json()
    assert data["auth_domain"] == "@tangentia.com"


def test_hr_login_success(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "hr.lead@tangentia.com", "password": "TangentiaHR@2026"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "hr.lead@tangentia.com"
    assert data["user"]["role"] == "hr_admin"

    # Verify access to HR endpoints using the returned JWT token
    token = data["access_token"]
    hr_res = client.get(
        "/api/hr/referrals",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert hr_res.status_code == 200


def test_hr_login_invalid_domain(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "hacker@external.com", "password": "TangentiaHR@2026"},
    )
    assert res.status_code == 400
    assert "@tangentia.com" in res.json()["detail"]


def test_hr_login_invalid_password(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "hr.lead@tangentia.com", "password": "WrongPassword123"},
    )
    assert res.status_code == 401
    assert "password incorrect" in res.json()["detail"].lower()


def test_hr_login_user_does_not_exist(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "nobody.atall@tangentia.com", "password": "SomePassword123"},
    )
    assert res.status_code == 401
    assert "user does not exist" in res.json()["detail"].lower()


def test_hr_login_employee_rejected(client):
    # Employee accounts must not be allowed to log into HR portal
    res = client.post(
        "/api/auth/login",
        json={"email": "employee@tangentia.com", "password": "somepassword"},
    )
    assert res.status_code in [401, 403]


def test_unauthenticated_request_rejected(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.payload"})
    assert res.status_code == 401


def test_employee_cannot_access_hr_endpoints(client):
    headers = {"Authorization": "Bearer dev-employee-token"}
    res = client.get("/api/hr/referrals", headers=headers)
    assert res.status_code == 403
    assert "HR / Administrator" in res.json()["detail"]


def test_hr_admin_can_access_hr_endpoints(client):
    headers = {"Authorization": "Bearer dev-hr-token"}
    res = client.get("/api/hr/referrals", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_hr_admin_can_access_analytics(client):
    headers = {"Authorization": "Bearer dev-hr-token"}
    res = client.get("/api/hr/analytics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_referrals" in data
    assert "funnel" in data


def test_password_hashing_and_verification():
    from app.services.auth_service import hash_password, verify_password
    plain = "TangentiaHR@2026"
    hashed = hash_password(plain)

    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    # Legacy plaintext backward compatibility
    assert verify_password(plain, plain) is True
    assert verify_password("WrongPassword", plain) is False


def test_production_environment_blocks_dev_backdoor_tokens(client, monkeypatch):
    from app.config import settings

    # Simulate production environment with proper JWT_SECRET_KEY configured
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DEV_MODE", False)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "production-test-secure-random-key-64-bytes")


    # Dev token should now be strictly rejected with 401
    headers = {"Authorization": "Bearer dev-hr-token"}
    res = client.get("/api/hr/referrals", headers=headers)
    assert res.status_code == 401

    headers_emp = {"Authorization": "Bearer dev-employee-token"}
    res_emp = client.get("/api/hr/referrals", headers=headers_emp)
    assert res_emp.status_code == 401

    # X-Dev-Role header bypass should also be strictly rejected
    res_header = client.get("/api/hr/referrals", headers={"X-Dev-Role": "hr_admin"})
    assert res_header.status_code == 401

