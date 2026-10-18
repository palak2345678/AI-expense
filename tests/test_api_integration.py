"""
Integration Tests for FastAPI Backend Endpoints & Database Persistence
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Fuzzy Logic" in data["engine"]


def test_list_expenses(client):
    response = client.get("/api/expenses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_filter_expenses_by_category(client):
    response = client.get("/api/expenses?category=Meals & Entertainment")
    assert response.status_code == 200
    data = response.json()
    for item in data:
        assert item["category"] == "Meals & Entertainment"


def test_stats_endpoint(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "totalExpenses" in data
    assert "totalAmount" in data
    assert "flaggedCount" in data
    assert "avgRiskScore" in data
    assert "moneySaved" in data


def test_create_expense_invokes_ai_audit_and_persists(client):
    import time
    ts = int(time.time())
    emp_name = f"Test Eng {ts}"
    payload = {
        "employee": emp_name,
        "department": "Engineering",
        "category": "Meals & Entertainment",
        "amount": 78.50,
        "date": "2026-10-16",
        "time": "12:45",
        "description": "Integration test lunch claim",
        "has_receipt": True,
        "receipt_hash": f"RCPT-TEST-{ts}"
    }
    response = client.post("/api/expenses", json=payload)
    assert response.status_code == 201
    created = response.json()

    assert created["employee"] == emp_name
    assert created["riskScore"] < 40
    assert created["riskLevel"] == "Low"
    assert created["status"] == "approved"
    assert "fuzzy_score" in created or "fuzzyScore" in created
    assert "reasons" in created

    # Verify persistent retrieval
    get_res = client.get(f"/api/expenses?search={emp_name}")
    assert get_res.status_code == 200
    found = [e for e in get_res.json() if e["id"] == created["id"]]
    assert len(found) == 1
    assert found[0]["amount"] == 78.50

    # Submitting the exact duplicate MUST now trigger the duplicate audit rule
    dup_res = client.post("/api/expenses", json=payload)
    assert dup_res.status_code == 201
    dup_created = dup_res.json()
    assert dup_created["riskScore"] >= 80
    assert dup_created["riskLevel"] == "High"
    assert dup_created["status"] == "flagged"
    assert any("Duplicate" in r for r in dup_created["reasons"])


def test_update_expense_status(client):
    # First get an expense
    res = client.get("/api/expenses")
    first_exp = res.json()[0]
    exp_id = first_exp["id"]

    # Patch status
    patch_res = client.patch(f"/api/expenses/{exp_id}/status", json={"status": "approved"})
    assert patch_res.status_code == 200
    assert patch_res.json()["updated"] is True

    # Verify updated in database
    verify_res = client.get(f"/api/expenses?search={exp_id}")
    updated = [e for e in verify_res.json() if e["id"] == exp_id][0]
    assert updated["status"] == "approved"


def test_auth_login_demo_user(client):
    response = client.post("/api/auth/login", json={"email": "auditor@auditai.com", "password": "Demo@123"})
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["role"] == "auditor"
    assert data["user"]["name"] == "Alex Vance"


def test_auth_login_dynamic_user(client):
    response = client.post("/api/auth/login", json={"email": "custom.tester@auditai.com", "password": "Demo@123"})
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == "custom.tester@auditai.com"


def test_auth_me_and_logout(client):
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "auditor@auditai.com"

    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
    assert "Logged out" in logout_res.json()["message"]


def test_pending_approvals(client):
    res = client.get("/api/approvals/pending")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_approve_and_reject_actions(client):
    # Retrieve an expense
    res = client.get("/api/expenses")
    exp_id = res.json()[0]["id"]

    # Test approve
    app_res = client.post(f"/api/expenses/{exp_id}/approve", json={"comment": "Approved by unit test"})
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "approved"

    # Test reject
    rej_res = client.post(f"/api/expenses/{exp_id}/reject", json={"comment": "Rejected by unit test"})
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"


def test_audit_logs(client):
    res = client.get("/api/audit-logs")
    assert res.status_code == 200
    data = res.json()
    assert "logs" in data
    assert len(data["logs"]) > 0


def test_ask_assistant(client):
    res = client.post("/api/assistant", json={"question": "What is the highest expense?"})
    assert res.status_code == 200
    assert "answer" in res.json()
    assert len(res.json()["answer"]) > 10


def test_serve_login_html(client):
    res = client.get("/login")
    assert res.status_code == 200
    assert "AuditAI Platform" in res.text or "Sign In" in res.text
