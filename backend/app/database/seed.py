"""Database seeding for default candidate profile, sources, and admin account."""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.models import (
    DiscoverySource,
    Project,
    Skill,
    UserAccount,
    UserProfile,
    UserSetting,
)


def seed_database(db: Session) -> None:
    settings = get_settings()

    # 1. Admin Account
    admin = db.query(UserAccount).filter(UserAccount.email == settings.admin_email).first()
    if not admin:
        admin = UserAccount(
            email=settings.admin_email,
            hashed_password=hash_password(settings.admin_password),
            full_name="Kanish K (Candidate Admin)",
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.flush()

    # 2. Candidate Profile (Exact specifications from User Prompt)
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile(
            full_name="Kanish K",
            education="B.E. Computer Science and Engineering",
            institution="Bannari Amman Institute of Technology",
            location="Coimbatore, Tamil Nadu, India",
            graduation_year=2028,
            current_status="Student / Internship candidate",
            target_career_positioning="AI Engineer",
            career_goal="20+ LPA placement target",
            career_interests=[
                "Artificial Intelligence",
                "Machine Learning",
                "Deep Learning",
                "Generative AI",
                "NLP",
                "AI Agents",
                "Python Backend Development",
                "Software Engineering",
                "Data Science",
            ],
            preferred_locations=["India", "Remote", "Hybrid"],
            cgpa=8.5,
            resume_summary=(
                "Third-year B.E. Computer Science student at Bannari Amman Institute of Technology graduating in 2028. "
                "Targeting AI Engineer roles with deep interests in GenAI, AI Agents, NLP, and Python backend development."
            ),
        )
        db.add(profile)
        db.flush()

        # Seed Skills
        initial_skills = [
            ("Python", "technical", "advanced"),
            ("Machine Learning", "technical", "intermediate"),
            ("Deep Learning", "technical", "intermediate"),
            ("NLP", "technical", "intermediate"),
            ("Generative AI", "technical", "intermediate"),
            ("FastAPI", "technical", "intermediate"),
            ("React", "technical", "intermediate"),
            ("TypeScript", "technical", "intermediate"),
            ("SQL", "technical", "intermediate"),
            ("Data Structures and Algorithms", "technical", "intermediate"),
            ("Git and GitHub", "technical", "advanced"),
        ]
        for name, cat, prof in initial_skills:
            db.add(Skill(profile_id=profile.id, name=name, category=cat, proficiency=prof))

        # Seed Projects and Achievements
        initial_projects = [
            (
                "Digital Twin of EHV Substation Monitoring",
                "Smart India Hackathon Winner",
                "Real-time monitoring and anomaly detection system for Extra High Voltage substations using digital twin architecture.",
                ["Python", "Machine Learning", "FastAPI", "React", "IoT"],
            ),
            (
                "Kiosk Management System",
                "CDAC Project Runner-up",
                "Secure, kiosk management automation framework with remote monitoring and centralized dispatch.",
                ["Python", "FastAPI", "SQL", "TypeScript"],
            ),
            (
                "Intelligent Multilingual Grievance Categorization and Automated Dispatch Framework",
                "Academic & Research Project",
                "NLP-driven system for categorizing citizen grievances in multiple Indic languages with automated department routing.",
                ["Python", "NLP", "Deep Learning", "Generative AI", "FastAPI"],
            ),
        ]
        for title, ach, desc, tech in initial_projects:
            db.add(
                Project(
                    profile_id=profile.id,
                    title=title,
                    achievement=ach,
                    description=desc,
                    tech_stack=tech,
                )
            )

    # 3. Default Discovery Sources (Permitted feeds, APIs, official portals)
    default_sources = [
        {
            "name": "Arxiv AI & ML Research Preprints",
            "adapter_key": "arxiv_research",
            "source_type": "api",
            "enabled": True,
            "frequency_hours": 24,
            "config_json": {
                "categories": ["cs.AI", "cs.LG", "cs.CL"],
                "url": "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=15",
            },
        },
        {
            "name": "Hugging Face Daily Papers & AI Research",
            "adapter_key": "huggingface_papers",
            "source_type": "api",
            "enabled": True,
            "frequency_hours": 24,
            "config_json": {
                "url": "https://huggingface.co/api/daily_papers",
            },
        },
        {
            "name": "RemoteOK AI & Python Software Feed",
            "adapter_key": "remoteok_feed",
            "source_type": "api",
            "enabled": True,
            "frequency_hours": 12,
            "config_json": {
                "url": "https://remoteok.com/api?tag=python",
            },
        },
        {
            "name": "Remotive Remote Software & AI Jobs",
            "adapter_key": "remotive_jobs",
            "source_type": "api",
            "enabled": True,
            "frequency_hours": 12,
            "config_json": {
                "url": "https://remotive.com/api/remote-jobs?category=software-dev&limit=25",
            },
        },
        {
            "name": "Arbeitnow Tech & Internships Board",
            "adapter_key": "arbeitnow_jobs",
            "source_type": "api",
            "enabled": True,
            "frequency_hours": 12,
            "config_json": {
                "url": "https://www.arbeitnow.com/api/job-board-api",
            },
        },
        {
            "name": "We Work Remotely - Programming & Internships",
            "adapter_key": "wwr_feed",
            "source_type": "rss_feed",
            "enabled": True,
            "frequency_hours": 12,
            "config_json": {
                "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
            },
        },
        {
            "name": "ML Contests & AI Hackathons Feed",
            "adapter_key": "generic_rss",
            "source_type": "rss_feed",
            "enabled": True,
            "frequency_hours": 24,
            "config_json": {
                "url": "https://mlcontests.com/rss.xml",
                "category_hint": "hackathons",
            },
        },
        {
            "name": "Class Central AI & Learning Programs",
            "adapter_key": "generic_rss",
            "source_type": "rss_feed",
            "enabled": True,
            "frequency_hours": 48,
            "config_json": {
                "url": "https://www.classcentral.com/report/feed/",
                "category_hint": "courses",
            },
        },
        {
            "name": "User-Submitted Public Post or URL",
            "adapter_key": "user_submitted",
            "source_type": "user_input",
            "enabled": True,
            "frequency_hours": 1,
            "config_json": {},
        },
    ]

    for src in default_sources:
        existing = db.query(DiscoverySource).filter(DiscoverySource.adapter_key == src["adapter_key"]).first()
        if not existing:
            db.add(DiscoverySource(**src))

    # 4. Default Settings (Scoring Weights)
    scoring_setting = db.query(UserSetting).filter(UserSetting.key == "scoring_weights").first()
    if not scoring_setting:
        db.add(
            UserSetting(
                key="scoring_weights",
                value={
                    "skill_match": 0.30,
                    "eligibility_match": 0.25,
                    "role_relevance": 0.20,
                    "location_preference": 0.10,
                    "referral_freshness": 0.15,
                    "high_match_threshold": 75,
                },
            )
        )

    db.commit()
