"""Live audit of application status accuracy on sampled opportunities."""

import asyncio
import random
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.models import Opportunity
from app.discovery.base import is_linkedin_url

async def inspect_url(url: str, timeout: int = 10):
    if not url:
        return {"status": "INVALID_URL", "final_url": None, "title": None, "has_app_link": False, "evidence": "Empty URL"}
    if is_linkedin_url(url):
        return {"status": "UNVERIFIED", "final_url": url, "title": "LinkedIn Opportunity", "has_app_link": False, "evidence": "LinkedIn public URL (bot access restricted)"}

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ReferralPilotAI/2.1 (Academic Career Audit Bot)"})
            final_url = str(resp.url)
            if resp.status_code in (404, 410):
                return {"status": "CLOSED", "final_url": final_url, "title": None, "has_app_link": False, "evidence": f"HTTP {resp.status_code} Not Found/Gone"}
            if resp.status_code >= 400:
                return {"status": "SOURCE_UNAVAILABLE", "final_url": final_url, "title": None, "has_app_link": False, "evidence": f"HTTP {resp.status_code}"}

            soup = BeautifulSoup(resp.text, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else None
            page_text = " ".join(soup.get_text(" ", strip=True).split()).lower()

            closure_phrases = [
                "this job has expired",
                "position has been filled",
                "no longer accepting applications",
                "applications are closed",
                "application deadline has passed",
                "this opportunity is closed",
                "registration closed",
                "contest has ended",
                "registration has ended",
                "event expired",
            ]
            for phrase in closure_phrases:
                if phrase in page_text:
                    return {"status": "CLOSED", "final_url": final_url, "title": title, "has_app_link": False, "evidence": f"Closure keyword found: '{phrase}'"}

            # Check application/registration link or action
            has_app_link = False
            for a in soup.find_all("a", href=True):
                href = a["href"].lower()
                text = a.get_text().strip().lower()
                if any(k in href or k in text for k in ["apply", "register", "submit application", "sign up to apply"]):
                    has_app_link = True
                    break

            if has_app_link or any(k in page_text for k in ["apply now", "register now", "application process", "eligible candidates can apply"]):
                return {"status": "OPEN", "final_url": final_url, "title": title, "has_app_link": has_app_link, "evidence": "Active application/registration form or button detected"}

            return {"status": "UNKNOWN", "final_url": final_url, "title": title, "has_app_link": False, "evidence": "HTTP 200 returned but explicit application call-to-action is ambiguous"}
    except Exception as e:
        return {"status": "SOURCE_UNAVAILABLE", "final_url": url, "title": None, "has_app_link": False, "evidence": f"Request failed: {str(e)[:60]}"}

async def main():
    db = SessionLocal()
    random.seed(42)  # Deterministic seed for reproducible audit

    # 15 Jobs
    jobs = db.query(Opportunity).filter(Opportunity.opportunity_type == "JOB").all()
    sample_jobs = random.sample(jobs, min(len(jobs), 15))

    # 15 Internships
    internships = db.query(Opportunity).filter(Opportunity.opportunity_type == "INTERNSHIP").all()
    sample_internships = random.sample(internships, min(len(internships), 15))

    # 10 Hackathons
    hackathons = db.query(Opportunity).filter(Opportunity.opportunity_type == "HACKATHON").all()
    sample_hackathons = random.sample(hackathons, min(len(hackathons), 10))

    # 10 Scholarships
    scholarships = db.query(Opportunity).filter(Opportunity.opportunity_type == "SCHOLARSHIP").all()
    sample_scholarships = random.sample(scholarships, min(len(scholarships), 10))

    categories = [
        ("JOB", sample_jobs),
        ("INTERNSHIP", sample_internships),
        ("HACKATHON", sample_hackathons),
        ("SCHOLARSHIP", sample_scholarships),
    ]

    total_audited = 0
    results_by_cat = {}

    for cat_name, samples in categories:
        print(f"\n=======================================================")
        print(f" AUDITING {len(samples)} {cat_name} OPPORTUNITIES")
        print(f"=======================================================")
        cat_results = []
        for i, opp in enumerate(samples, 1):
            url = opp.application_url or opp.source_url
            audit = await inspect_url(url)
            cat_results.append({
                "id": opp.id,
                "title": opp.title,
                "org": opp.organization,
                "source_url": url,
                "final_url": audit["final_url"],
                "deadline": opp.deadline.isoformat() if opp.deadline else "None specified",
                "db_status": opp.application_status,
                "audited_status": audit["status"],
                "evidence": audit["evidence"],
                "last_verified_at": opp.last_verified_at.isoformat() if opp.last_verified_at else "Not recorded",
            })
            print(f"[{i:02d}] ID:{opp.id} | {opp.title[:38]} | {opp.organization[:18]}")
            print(f"     URL: {url}")
            print(f"     Final URL: {audit['final_url']}")
            print(f"     Deadline: {opp.deadline.isoformat() if opp.deadline else 'None specified'}")
            print(f"     DB Status: {opp.application_status} -> Audited Status: {audit['status']}")
            print(f"     Evidence: {audit['evidence']}")
            print()
            total_audited += 1

        results_by_cat[cat_name] = cat_results

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
