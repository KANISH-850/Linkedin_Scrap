"""Comprehensive tests covering ReferralPilot AI acceptance scenarios."""

from datetime import date, timedelta
import pytest

from app.ai.heuristic import HeuristicIntelligenceEngine
from app.discovery.adapters import process_manual_submission
from app.discovery.base import canonicalize_url, compute_dedup_hash, is_linkedin_url
from app.models.models import DiscoveryRun
from app.telegram.service import telegram_service


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["app"] == "ReferralPilot AI"


def test_unauthenticated_access_rejected(client):
    assert client.get("/api/profile").status_code == 401
    assert client.get("/api/opportunities").status_code == 401
    assert client.post("/api/discovery/run").status_code == 401


def test_profile_seeded_and_editable(client, auth_headers):
    resp = client.get("/api/profile", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["graduation_year"] == 2028
    assert data["institution"] == "Bannari Amman Institute of Technology"
    assert len(data["skills"]) >= 10
    assert len(data["projects"]) == 3

    # Update profile
    upd = client.put(
        "/api/profile",
        headers=auth_headers,
        json={"career_goal": "25+ LPA AI Engineer target"},
    )
    assert upd.status_code == 200
    assert upd.json()["career_goal"] == "25+ LPA AI Engineer target"


def test_deduplication_preserves_distinct_roles():
    h1 = compute_dedup_hash("Google", "AI Engineering Intern", "internships", "https://careers.google.com/1")
    h2 = compute_dedup_hash("Google", "Software Engineering Intern", "internships", "https://careers.google.com/2")
    h1_dup = compute_dedup_hash("Google", "AI Engineering Intern", "internships", "https://careers.google.com/1?utm_source=x")
    assert h1 != h2
    assert h1 == h1_dup
    assert canonicalize_url("https://example.com/job/?utm_source=rss&ref=123") == "https://example.com/job"


@pytest.mark.asyncio
async def test_linkedin_compliance_guard():
    assert is_linkedin_url("https://www.linkedin.com/jobs/view/12345") is True
    with pytest.raises(ValueError, match="LinkedIn scraping is disabled"):
        await process_manual_submission(url="https://www.linkedin.com/posts/12345", raw_text=None)

    # Submitting with pasted text succeeds without scraping LinkedIn
    raw = await process_manual_submission(
        url="https://www.linkedin.com/posts/12345",
        raw_text="We are hiring an AI Engineer Intern at Acme AI! I can refer you if you know Python and FastAPI.",
        organization_hint="Acme AI",
    )
    assert raw.organization == "Acme AI"
    assert "Python" in raw.description


@pytest.mark.asyncio
async def test_eligibility_graduation_year_and_referral_classification():
    engine = HeuristicIntelligenceEngine()
    profile = {
        "graduation_year": 2028,
        "target_career_positioning": "AI Engineer",
        "skills": ["Python", "Machine Learning", "FastAPI", "NLP"],
    }
    weights = {
        "skill_match": 0.30,
        "eligibility_match": 0.25,
        "role_relevance": 0.20,
        "location_preference": 0.10,
        "referral_freshness": 0.15,
    }

    # Case 1: Mandatory 2026 batch restriction -> Not eligible
    ext_2026 = await engine.extract_and_classify(
        "Hiring Software Engineer Intern. Only 2026 batch graduates eligible. Apply here.",
        "Software Engineer Intern",
        {"category_hint": "internships", "organization": "TechCorp"},
    )
    assert ext_2026.referral_classification in ("GENERAL_JOB_POST", "general_job_announcement")
    elig, score = await engine.evaluate_eligibility_and_score(
        profile,
        {
            "title": "Software Engineer Intern",
            "organization": "TechCorp",
            "category": "internships",
            "description": "Only 2026 batch graduates eligible.",
            "location": "India",
            "is_remote": False,
            "required_skills": ["Python"],
            "graduation_year_requirement": ext_2026.graduation_year_requirement,
            "referral_classification": ext_2026.referral_classification,
        },
        weights,
    )
    assert elig.status == "Not eligible"
    assert score.overall_score <= 45.0

    # Case 2: Confirmed referral offer + matching skills + Remote
    ext_ref = await engine.extract_and_classify(
        "Happy to refer for AI Engineer Intern! DM me for referral. Skills: Python, FastAPI, NLP. Remote.",
        "AI Engineer Intern",
        {"category_hint": "referrals", "organization": "NeuralLabs"},
    )
    assert ext_ref.referral_classification in ("CONFIRMED_REFERRAL_OFFER", "confirmed_referral_offer")
    elig2, score2 = await engine.evaluate_eligibility_and_score(
        profile,
        {
            "title": "AI Engineer Intern",
            "organization": "NeuralLabs",
            "category": "referrals",
            "description": "Happy to refer for AI Engineer Intern!",
            "location": "Remote",
            "is_remote": True,
            "required_skills": ["Python", "FastAPI", "NLP"],
            "referral_classification": ext_ref.referral_classification,
        },
        weights,
    )
    assert elig2.status == "Eligible"
    assert score2.overall_score >= 85.0


@pytest.mark.asyncio
async def test_draft_message_no_false_claims():
    engine = HeuristicIntelligenceEngine()
    profile = {
        "full_name": "Kanish K",
        "institution": "Bannari Amman Institute of Technology",
    }
    opp = {"title": "AI Engineer Intern", "organization": "OpenAI"}
    conn = await engine.draft_message(profile, opp, "connection_request")
    assert len(conn.body) <= 300
    assert "Bannari Amman Institute of Technology" in conn.body

    ref = await engine.draft_message(profile, opp, "referral_request")
    assert "AI Engineer Intern" in ref.body
    assert "OpenAI" in ref.body


def test_manual_submission_status_followup_application_flow(client, auth_headers):
    # Submit manual opportunity
    sub = client.post(
        "/api/discovery/submit",
        headers=auth_headers,
        json={
            "url": "https://www.linkedin.com/posts/sample-ai-intern",
            "raw_text": "I can refer for GenAI Intern at DeepTech India! Skills: Python, Generative AI, FastAPI. Remote.",
            "title_hint": "GenAI Intern",
            "organization_hint": "DeepTech India",
            "category_hint": "referrals",
        },
    )
    assert sub.status_code == 200
    opp_id = sub.json()["id"]
    assert sub.json()["deadline"] is None  # Never fabricated

    # Duplicate submission does not create a second opportunity
    sub2 = client.post(
        "/api/discovery/submit",
        headers=auth_headers,
        json={
            "url": "https://www.linkedin.com/posts/sample-ai-intern",
            "raw_text": "I can refer for GenAI Intern at DeepTech India! Skills: Python, Generative AI, FastAPI. Remote.",
            "title_hint": "GenAI Intern",
            "organization_hint": "DeepTech India",
            "category_hint": "referrals",
        },
    )
    assert sub2.status_code == 200
    assert sub2.json()["id"] == opp_id

    # Update status
    st = client.patch(
        f"/api/opportunities/{opp_id}/status",
        headers=auth_headers,
        json={"tracking_status": "CONNECTION_PENDING", "is_interested": True, "note": "Sent connection request"},
    )
    assert st.status_code == 200
    assert st.json()["tracking_status"] == "CONNECTION_PENDING"
    assert len(st.json()["status_history"]) == 1

    # Add follow-up
    due = (date.today() + timedelta(days=3)).isoformat()
    fup = client.post(
        f"/api/opportunities/{opp_id}/follow-up",
        headers=auth_headers,
        json={"due_date": due, "notes": "Follow up if no reply"},
    )
    assert fup.status_code == 200
    assert len(client.get("/api/follow-ups", headers=auth_headers).json()) == 1

    # Draft message
    draft = client.post(
        f"/api/opportunities/{opp_id}/draft-message",
        headers=auth_headers,
        json={"draft_type": "referral_request", "contact_name": "Priya"},
    )
    assert draft.status_code == 200
    assert "Priya" in draft.json()["body"]

    # Reply analysis
    rep = client.post(
        "/api/replies/analyze",
        headers=auth_headers,
        json={"opportunity_id": opp_id, "reply_text": "Sure, please send your resume over!"},
    )
    assert rep.status_code == 200
    assert rep.json()["classification"] == "Resume requested"

    # Record application
    app_res = client.post(
        "/api/applications",
        headers=auth_headers,
        json={"opportunity_id": opp_id, "resume_version": "AI_Resume_v3.pdf"},
    )
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPLIED"


def test_telegram_webhook_security_and_idempotency(client):
    # Wrong webhook secret -> 403
    bad_sec = client.post(
        "/api/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
        json={"update_id": 1, "message": {"chat": {"id": 999888777}, "from": {"id": 999888777}, "text": "/start"}},
    )
    assert bad_sec.status_code == 403

    # Unauthorized user -> rejected
    unauth = client.post(
        "/api/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-webhook-secret"},
        json={"update_id": 2, "message": {"chat": {"id": 111222333}, "from": {"id": 111222333}, "text": "/today"}},
    )
    assert unauth.status_code == 200
    assert unauth.json()["ok"] is False
    assert unauth.json()["reason"] == "unauthorized"

    # Authorized user -> processed
    ok = client.post(
        "/api/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-webhook-secret"},
        json={"update_id": 3, "message": {"chat": {"id": 999888777}, "from": {"id": 999888777}, "text": "/today"}},
    )
    assert ok.status_code == 200
    assert ok.json()["ok"] is True

    # Duplicate update_id -> idempotent
    dup = client.post(
        "/api/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-webhook-secret"},
        json={"update_id": 3, "message": {"chat": {"id": 999888777}, "from": {"id": 999888777}, "text": "/today"}},
    )
    assert dup.status_code == 200
    assert dup.json().get("duplicate") is True


@pytest.mark.asyncio
async def test_daily_digest_logged_even_with_zero_new_opportunities(db_session):
    run = DiscoveryRun(
        status="completed",
        trigger_type="scheduled_cron",
        sources_checked=3,
        sources_failed=0,
        opportunities_discovered=0,
        new_opportunities=0,
        high_match_count=0,
        errors_json=[],
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    # Even without TELEGRAM_BOT_TOKEN set in unit tests, Notification record is created & deduplicated
    await telegram_service.send_daily_digest(db_session, run)
    from app.models.models import Notification
    notifs = db_session.query(Notification).filter(Notification.discovery_run_id == run.id).all()
    assert len(notifs) == 1
    assert notifs[0].notification_type == "daily_digest"

