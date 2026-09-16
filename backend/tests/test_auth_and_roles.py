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
