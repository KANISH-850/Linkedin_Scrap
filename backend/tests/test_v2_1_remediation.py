"""Regression and remediation test suite for ReferralPilot AI V2.1.
Verifies:
1. All 10 referral classification test strings with exact classifications and supporting text.
2. Research papers vs job vacancies separation (opportunity_type and application_status).
3. Active vs closed job verification (closure phrase detection).
4. Indian student relevance scoring (Bangalore/Hyderabad/Chennai/Coimbatore, 2028 batch boost, senior role demotion).
5. Unstop Scholarships adapter functionality.
"""

from datetime import date
import pytest

from app.ai.heuristic import HeuristicIntelligenceEngine
from app.discovery.adapters import ArxivResearchAdapter, UnstopAdapter
from app.discovery.base import VerificationState, verify_url_deep
from app.discovery.base import RawOpportunity
from app.models.models import Opportunity, OpportunityScore


@pytest.mark.asyncio
async def test_referral_classification_10_cases():
    engine = HeuristicIntelligenceEngine()

    test_cases = [
        # 1. Confirmed referral offer
        (
            "I can refer candidates for this role.",
            "CONFIRMED_REFERRAL_OFFER",
            "i can refer",
        ),
        # 2. Confirmed referral offer variant
        (
            "DM me for a referral.",
            "CONFIRMED_REFERRAL_OFFER",
            "dm me",
        ),
        # 3. Third-party vacancy announcement without personal offer
        (
            "Google is hiring AI interns.",
            "GENERAL_JOB_POST",
            "google is hiring",
        ),
        # 4. Job post asking candidate to apply online (not a referral offer)
        (
            "Apply through this link.",
            "GENERAL_JOB_POST",
            "apply through",
        ),
        # 5. Candidate asking for a referral (explicit referral request)
        (
            "Does anyone have a referral?",
            "EXPLICIT_REFERRAL_REQUEST",
            "does anyone have a referral",
        ),
        # 6. Hiring announcement
        (
            "Hiring for multiple engineering positions.",
            "HIRING_ANNOUNCEMENT",
            "hiring for multiple",
        ),
        # 7. Unclear text with no keywords
        (
            "Unclear text with no keywords.",
            "UNCLEAR",
            None,
        ),
        # 8. Past referral mention by applicant (must not become CONFIRMED_REFERRAL_OFFER)
        (
            "I received a referral from my friend.",
            "UNCLEAR",
            "past referral",
        ),
        # 9. Direct message referral invitation
        (
            "DM me if you need a referral.",
            "CONFIRMED_REFERRAL_OFFER",
            "dm me if you need a referral",
        ),
        # 10. General corporate referral policy without personal author offer
        (
            "Referral program available at our company.",
            "UNCLEAR",
            "corporate referral",
        ),
    ]

    for text, expected_cls, expected_excerpt_kw in test_cases:
        res = await engine.extract_and_classify(text, "Test Opportunity", {})
        assert res.referral_classification == expected_cls, (
            f"Failed on text: '{text}'. Expected {expected_cls}, got {res.referral_classification}"
        )
        if expected_excerpt_kw:
            assert res.referral_evidence_excerpt is not None, f"Expected supporting text for '{text}'"
            assert expected_excerpt_kw.lower() in res.referral_evidence_excerpt.lower(), (
                f"Expected '{expected_excerpt_kw}' in '{res.referral_evidence_excerpt}'"
            )


@pytest.mark.asyncio
async def test_research_paper_separation():
    adapter = ArxivResearchAdapter()
    config = {
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=2",
        "categories": ["cs.AI"],
    }
    raw_opps = await adapter.fetch(config)
    assert len(raw_opps) > 0
    for opp in raw_opps:
        assert opp.opportunity_type == "RESEARCH_PAPER"
        assert opp.application_status == "NOT_APPLICABLE"


@pytest.mark.asyncio
async def test_closed_job_verification(respx_mock):
    # Closure text detection
    respx_mock.get("https://example.com/jobs/closed-1").respond(
        status_code=200,
        text="<html><head><title>Job Closed</title></head><body><h1>Software Engineer</h1><p>This position is closed and no longer accepting applications.</p></body></html>",
    )
    status, title, _ = await verify_url_deep("https://example.com/jobs/closed-1")
    assert status == VerificationState.CLOSED
    assert title == "Job Closed"

    # 404/410 detection
    respx_mock.get("https://example.com/jobs/expired-404").respond(status_code=404)
    status_404, _, _ = await verify_url_deep("https://example.com/jobs/expired-404")
    assert status_404 == VerificationState.CLOSED


@pytest.mark.asyncio
async def test_indian_student_relevance_and_senior_demotion():
    engine = HeuristicIntelligenceEngine()
    profile = {
        "graduation_year": 2028,
        "target_career_positioning": "AI Engineer",
        "institution": "Bannari Amman Institute of Technology",
        "skills": ["Python", "Machine Learning", "FastAPI", "PyTorch"],
    }
    weights = {
        "skill_match": 0.30,
        "eligibility_match": 0.25,
        "role_relevance": 0.20,
        "location_preference": 0.10,
        "referral_freshness": 0.15,
    }

    # Case A: Senior position -> Must be disqualified / score < 50
    senior_opp = {
        "title": "Senior AI Architect (10+ years experience)",
        "organization": "MegaCorp",
        "category": "jobs",
        "opportunity_type": "JOB",
        "location": "Bangalore, India",
        "experience_requirement": "8+ years",
        "required_skills": ["Python", "PyTorch"],
        "description": "Lead enterprise AI transformation. 10+ years in distributed ML required.",
    }
    elig_sr, score_sr = await engine.evaluate_eligibility_and_score(profile, senior_opp, weights)
    assert elig_sr.status == "Not eligible"
    assert score_sr.overall_score < 50.0
    assert any("senior" in r.lower() for r in elig_sr.disqualifying_requirements)

    # Case B: Coimbatore / Bangalore Student Intern -> High score
    intern_opp = {
        "title": "AI Research Intern (Batch 2028 / Pre-final year)",
        "organization": "TCS Research",
        "category": "internships",
        "opportunity_type": "INTERNSHIP",
        "location": "Coimbatore, Tamil Nadu, India",
        "required_skills": ["Python", "Machine Learning", "PyTorch"],
        "description": "Looking for pre-final year B.E./B.Tech students graduating in 2028. Work on LLMs.",
    }
    elig_int, score_int = await engine.evaluate_eligibility_and_score(profile, intern_opp, weights)
    assert elig_int.status == "Eligible"
    assert score_int.overall_score >= 80.0
    assert score_int.location_score == 100.0


@pytest.mark.asyncio
async def test_unstop_scholarships_adapter():
    adapter = UnstopAdapter()
    config = {
        "url": "https://unstop.com/api/public/opportunity/search-result?opportunity=scholarships&per_page=5",
        "opportunity_type": "scholarships",
    }
    opps = await adapter.fetch(config)
    assert len(opps) > 0
    for o in opps:
        assert o.opportunity_type == "SCHOLARSHIP"
        assert o.application_status in ("OPEN", "EXPIRED", "UNVERIFIED")
        assert o.source_url.startswith("https://")
