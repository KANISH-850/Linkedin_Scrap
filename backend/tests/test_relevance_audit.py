"""Auditing relevance ranking across 6 distinct opportunity scenarios for 2028 Indian undergrad."""

import pytest
from app.ai.heuristic import HeuristicIntelligenceEngine

@pytest.mark.asyncio
async def test_relevance_ranking_six_scenarios():
    engine = HeuristicIntelligenceEngine()
    profile = {
        "full_name": "Kanish K",
        "institution": "Bannari Amman Institute of Technology",
        "graduation_year": 2028,
        "target_career_positioning": "AI Engineer",
        "skills": ["Python", "PyTorch", "FastAPI", "Machine Learning", "Generative AI", "Docker", "Git"],
    }
    weights = {
        "skill_match": 0.30,
        "eligibility_match": 0.25,
        "role_relevance": 0.20,
        "location_preference": 0.10,
        "referral_freshness": 0.15,
    }

    # 1. Excellent remote AI internship available to Indian students
    opp1 = {
        "title": "AI & Generative AI Intern (Batch 2028)",
        "organization": "NeuralLabs",
        "category": "internships",
        "opportunity_type": "INTERNSHIP",
        "location": "Remote (India)",
        "is_remote": True,
        "graduation_year_requirement": "2028 batch",
        "required_skills": ["Python", "PyTorch", "Generative AI", "FastAPI"],
        "description": "Building LLM agent workflows. Open to 3rd year students graduating in 2028 across India.",
    }
    elig1, score1 = await engine.evaluate_eligibility_and_score(profile, opp1, weights)
    assert elig1.status == "Eligible"
    assert score1.overall_score >= 85.0
    assert score1.skill_score == 100.0

    # 2. Average Coimbatore software internship (candidate in Coimbatore, but generic skills)
    opp2 = {
        "title": "Software Development Intern",
        "organization": "LocalTech Coimbatore",
        "category": "internships",
        "opportunity_type": "INTERNSHIP",
        "location": "Coimbatore, Tamil Nadu",
        "is_remote": False,
        "required_skills": ["Java", "Spring Boot", "MySQL"],
        "description": "General enterprise application development internship in Coimbatore.",
    }
    elig2, score2 = await engine.evaluate_eligibility_and_score(profile, opp2, weights)
    # Coimbatore location gets 100 location score, but skill score & relevance are lower than AI role
    assert score2.location_score == 100.0
    assert score2.overall_score < score1.overall_score
    assert score2.overall_score >= 50.0

    # 3. Senior AI engineer role (high skill overlap, but requires 8+ years)
    opp3 = {
        "title": "Senior AI Architect (10+ years experience)",
        "organization": "MegaCorp India",
        "category": "fresher_jobs",
        "opportunity_type": "JOB",
        "location": "Bangalore, India",
        "is_remote": False,
        "experience_requirement": "8+ years of experience",
        "required_skills": ["Python", "PyTorch", "Machine Learning"],
        "description": "Lead enterprise ML architecture. Minimum 8+ years experience in distributed ML.",
    }
    elig3, score3 = await engine.evaluate_eligibility_and_score(profile, opp3, weights)
    assert elig3.status == "Not eligible"
    assert score3.overall_score < 50.0
    assert any("senior" in r.lower() or "experience" in r.lower() for r in elig3.disqualifying_requirements)

    # 4. Fresher Python developer job in Bangalore
    opp4 = {
        "title": "Junior Python / Backend Developer (Fresher 2028)",
        "organization": "FinTech Bangalore",
        "category": "fresher_jobs",
        "opportunity_type": "JOB",
        "location": "Bangalore, India",
        "is_remote": False,
        "graduation_year_requirement": "2028 batch",
        "required_skills": ["Python", "FastAPI", "Docker"],
        "description": "Hiring 2028 graduates for backend engineering.",
    }
    elig4, score4 = await engine.evaluate_eligibility_and_score(profile, opp4, weights)
    assert elig4.status == "Eligible"
    assert score4.overall_score >= 75.0
    assert score4.overall_score > score3.overall_score

    # 5. Foreign onsite internship that excludes Indian applicants (requires US work authorization / no visa sponsorship)
    opp5 = {
        "title": "Machine Learning Intern",
        "organization": "Silicon Valley Defense AI",
        "category": "internships",
        "opportunity_type": "INTERNSHIP",
        "location": "San Francisco, CA, USA",
        "is_remote": False,
        "required_skills": ["Python", "PyTorch"],
        "description": "Must be a US citizen. Security clearance required. No visa sponsorship provided. Onsite in SF.",
    }
    elig5, score5 = await engine.evaluate_eligibility_and_score(profile, opp5, weights)
    assert elig5.status == "Not eligible"
    assert score5.overall_score < 50.0
    assert any("citizenship" in r.lower() or "authorization" in r.lower() for r in elig5.disqualifying_requirements)

    # 6. Global remote opportunity with unknown / unstated eligibility
    opp6 = {
        "title": "Open Source Contributor",
        "organization": "Global OSS Project",
        "category": "internships",
        "opportunity_type": "INTERNSHIP",
        "location": "Remote",
        "is_remote": True,
        "required_skills": [],
        "description": "Collaborate with open source mentors on community projects.",
    }
    elig6, score6 = await engine.evaluate_eligibility_and_score(profile, opp6, weights)
    # Must NOT be falsely marked fully eligible
    assert elig6.status != "Eligible"
    assert "verify" in elig6.status.lower() or "potentially" in elig6.status.lower()
    assert len(elig6.verification_questions) > 0
