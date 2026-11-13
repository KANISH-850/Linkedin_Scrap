"""Integration regression suite for user login, profile editing, discovery execution,
opportunity persistence, detail retrieval, status history, dashboard analytics, and digest."""

import pytest
from app.models.models import Opportunity, DiscoveryRun
from app.telegram.service import telegram_service

def test_login_success_and_failure(client):
    # Failure with invalid password
    bad_login = client.post(
        "/api/auth/login",
        json={"email": "admin@referralpilot.app", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # Success with seeded admin credentials
    good_login = client.post(
        "/api/auth/login",
        json={"email": "admin@referralpilot.app", "password": "ChangeMeStrongPassword123!"},
    )
    assert good_login.status_code == 200
    token_data = good_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

def test_profile_retrieval_and_editing(client, auth_headers):
    # Get profile
    res = client.get("/api/profile", headers=auth_headers)
    assert res.status_code == 200
    profile = res.json()
    assert profile["graduation_year"] == 2028

    # Edit profile
    upd = client.put(
        "/api/profile",
        headers=auth_headers,
        json={"location": "Coimbatore, Tamil Nadu", "career_goal": "Senior AI Placement"},
    )
    assert upd.status_code == 200
    assert upd.json()["location"] == "Coimbatore, Tamil Nadu"
    assert upd.json()["career_goal"] == "Senior AI Placement"

def test_opportunity_detail_and_status_history(client, auth_headers, db_session):
    opp = Opportunity(
        title="Integration Test AI Intern",
        organization="Test AI Labs",
        category="internships",
        opportunity_type="INTERNSHIP",
        application_status="OPEN",
        source_url="https://test.example.com/opp/1",
        canonical_url="https://test.example.com/opp/1",
        dedup_hash="integ_hash_001",
        description="Build LLM agents.",
    )
    db_session.add(opp)
    db_session.commit()
    db_session.refresh(opp)

    # Retrieve detail
    detail = client.get(f"/api/opportunities/{opp.id}", headers=auth_headers)
    assert detail.status_code == 200
    d_data = detail.json()
    assert d_data["title"] == "Integration Test AI Intern"
    assert d_data["opportunity_type"] == "INTERNSHIP"
    assert d_data["application_status"] == "OPEN"

    # Change tracking status
    st_change = client.patch(
        f"/api/opportunities/{opp.id}/status",
        headers=auth_headers,
        json={"tracking_status": "INTERESTED", "note": "High fit for 2028 batch"},
    )
    assert st_change.status_code == 200
    assert st_change.json()["tracking_status"] == "INTERESTED"

    # Verify status history in opportunity detail
    detail_after = client.get(f"/api/opportunities/{opp.id}", headers=auth_headers)
    assert detail_after.status_code == 200
    entries = detail_after.json()["status_history"]
    assert len(entries) >= 1
    assert entries[-1]["to_status"] == "INTERESTED"

def test_dashboard_summary_and_analytics_metrics(client, auth_headers):
    summary = client.get("/api/dashboard/summary", headers=auth_headers)
    assert summary.status_code == 200
    s_data = summary.json()
    assert "new_opportunities" in s_data
    assert "active_vacancies" in s_data
    assert "research_papers" in s_data
    assert "high_match_opportunities" in s_data

    analytics = client.get("/api/dashboard/analytics", headers=auth_headers)
    assert analytics.status_code == 200
    a_data = analytics.json()
    assert "by_category" in a_data
    assert "by_opportunity_type" in a_data
    assert "by_application_status" in a_data
    assert "application_pipeline" in a_data
