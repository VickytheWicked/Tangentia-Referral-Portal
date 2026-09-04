import pytest
from app.models.user import UserRole


def test_get_auth_config(client):
    res = client.get("/api/auth/config")
    assert res.status_code == 200
    data = res.json()
    assert "tenant_id" in data
    assert "authority" in data


def test_unauthenticated_request_rejected(client):
    # In strict non-dev mode, requests without token are 401
    # Test with invalid bearer token
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
