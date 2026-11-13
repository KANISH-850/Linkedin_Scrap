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
            "I'm referring for SWE-2 at Stripe! DM me your resume if interested.",
            "CONFIRMED_REFERRAL_OFFER",
            "referring",
        ),
        # 2. Confirmed referral offer variant
        (
            "DM me for a referral to our machine learning team at Uber.",
            "CONFIRMED_REFERRAL_OFFER",
            "dm me",
        ),
        # 3. Confirmed referral offer variant
        (
            "Happy to refer qualified candidates for backend roles at Datadog. Send message.",
            "CONFIRMED_REFERRAL_OFFER",
            "happy to refer",
        ),
        # 4. Job post asking candidate to apply online (not a referral offer)
        (
            "We are hiring senior backend engineers. Apply at careers.acme.com/job/123",
            "GENERAL_JOB_POST",
            None,
        ),
        # 5. Candidate asking for a referral (explicit referral request)
        (
            "Looking for a referral at Microsoft for SDE-1 role. Please DM if you can help!",
            "EXPLICIT_REFERRAL_REQUEST",
            "looking for a referral",
        ),
        # 6. Candidate asking for a referral variant
        (
            "Can anyone refer me for an AI internship at Google? Highly appreciate any help.",
            "EXPLICIT_REFERRAL_REQUEST",
            "refer me",
        ),
        # 7. Hiring announcement without personal referral offer
        (
            "Zomato is hiring Software Engineers across all levels for Gurgaon office.",
            "HIRING_ANNOUNCEMENT",
            "zomato is hiring",
        ),
        # 8. Hiring announcement variant
        (
            "Excited to announce our startup is hiring 10 full-stack engineers in Bangalore!",
            "HIRING_ANNOUNCEMENT",
            "is hiring",
        ),
        # 9. Career advice / general article (unclear / general)
        (
            "How to prepare for system design interviews in 2026: a comprehensive guide.",
            "UNCLEAR",
            None,
        ),
        # 10. General job post without referral keywords
        (
            "Frontend Developer role open at Canva. React, TypeScript, Tailwind required.",
            "GENERAL_JOB_POST",
            None,
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
        assert o.application_status == "OPEN"
        assert o.source_url.startswith("https://")
