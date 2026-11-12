"""Permitted public source adapters for ReferralPilot AI."""

from datetime import datetime, timezone
from typing import Any, List
from bs4 import BeautifulSoup
import feedparser
import httpx

from app.core.logging import get_logger
from app.discovery.base import BaseSourceAdapter, RawOpportunity, is_linkedin_url

logger = get_logger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "ReferralPilotAI/1.0 (+https://github.com/referralpilot-ai; personal career assistant)",
    "Accept": "application/json, application/xml, text/html, */*",
}


def _strip_html(html_text: str) -> str:
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return " ".join(soup.get_text(" ", strip=True).split())


def _infer_job_category(title: str, description: str, tags: List[str] | None = None) -> str:
    text = f"{title} {description} {' '.join(tags or [])}".lower()
    if any(k in text for k in ["intern", "internship", "summer trainee", "student program"]):
        return "internships"
    if any(k in text for k in ["hackathon", "ideathon", "innovation challenge", "codefest"]):
        return "hackathons"
    if any(k in text for k in ["scholarship", "fellowship", "grant", "bursary"]):
        return "scholarships"
    if any(k in text for k in ["research", "arxiv", "preprint", "faculty", "phd", "lab"]):
        return "research"
    if any(k in text for k in ["course", "certification", "bootcamp", "nanodegree"]):
        return "courses"
    if any(k in text for k in ["referral", "refer ", "dm for referral", "reach out for referral"]):
        return "referrals"
    return "fresher_jobs"


class RemotiveAdapter(BaseSourceAdapter):
    """Fetches remote software/AI jobs & internships from Remotive's public API."""

    adapter_key = "remotive_jobs"
    source_name = "Remotive Public Jobs API"
    source_type = "api"

    async def fetch(
        self,
        config: dict[str, Any],
        timeout: int = 15,
        max_items: int = 25,
    ) -> List[RawOpportunity]:
        url = config.get("url") or "https://remotive.com/api/remote-jobs?category=software-dev&limit=25"
        if is_linkedin_url(url):
            raise ValueError("LinkedIn URLs are not permitted in automated adapters.")

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=DEFAULT_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        jobs = data.get("jobs", [])[:max_items]
        results: List[RawOpportunity] = []
        for job in jobs:
            title = job.get("title") or "Untitled Role"
            company = job.get("company_name") or "Not specified"
            desc = _strip_html(job.get("description") or "")
            tags = job.get("tags") or []
            loc = job.get("candidate_required_location") or "Remote"
            job_url = job.get("url") or ""
            pub_date = None
            if job.get("publication_date"):
                try:
                    pub_date = datetime.fromisoformat(job["publication_date"].replace("Z", "+00:00"))
                except Exception:
                    pub_date = None

            cat = _infer_job_category(title, desc, tags)
            results.append(
                RawOpportunity(
                    title=title,
                    organization=company,
                    description=desc[:4000],
                    source_url=job_url,
                    application_url=job_url,
                    category_hint=cat,
                    location=loc,
                    is_remote=True,
                    posted_at=pub_date,
                    external_id=str(job.get("id") or job_url),
                    required_skills=[str(t) for t in tags[:10]],
                    compensation_or_stipend=job.get("salary") or None,
                    raw_payload={"id": job.get("id"), "job_type": job.get("job_type"), "tags": tags},
                )
            )
        return results


class ArbeitnowAdapter(BaseSourceAdapter):
    """Fetches public tech & internship listings from Arbeitnow's public API."""

    adapter_key = "arbeitnow_jobs"
    source_name = "Arbeitnow Public Job Board API"
    source_type = "api"

    async def fetch(
        self,
        config: dict[str, Any],
        timeout: int = 15,
        max_items: int = 25,
    ) -> List[RawOpportunity]:
        url = config.get("url") or "https://www.arbeitnow.com/api/job-board-api"
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=DEFAULT_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("data", [])[:max_items]
        results: List[RawOpportunity] = []
        for item in items:
            title = item.get("title") or "Untitled Role"
            company = item.get("company_name") or "Not specified"
            desc = _strip_html(item.get("description") or "")
            tags = item.get("tags") or []
            is_remote = bool(item.get("remote"))
            loc = item.get("location") or ("Remote" if is_remote else "Not specified")
            job_url = item.get("url") or ""
            pub_date = None
            if item.get("created_at"):
                try:
                    pub_date = datetime.fromtimestamp(int(item["created_at"]), tz=timezone.utc)
                except Exception:
                    pub_date = None

            results.append(
                RawOpportunity(
                    title=title,
                    organization=company,
                    description=desc[:4000],
                    source_url=job_url,
                    application_url=job_url,
                    category_hint=_infer_job_category(title, desc, tags),
                    location=loc,
                    is_remote=is_remote,
                    posted_at=pub_date,
                    external_id=str(item.get("slug") or job_url),
                    required_skills=[str(t) for t in tags[:10]],
                    raw_payload={"slug": item.get("slug"), "tags": tags},
                )
            )
        return results


class RemoteOKAdapter(BaseSourceAdapter):
    """Fetches Python & AI remote roles from RemoteOK public API."""

    adapter_key = "remoteok_feed"
    source_name = "RemoteOK Public API"
    source_type = "api"

    async def fetch(
        self,
        config: dict[str, Any],
        timeout: int = 15,
        max_items: int = 25,
    ) -> List[RawOpportunity]:
        url = config.get("url") or "https://remoteok.com/api?tag=python"
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=DEFAULT_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        items = [row for row in data if isinstance(row, dict) and row.get("position")][:max_items]
        results: List[RawOpportunity] = []
        for item in items:
            title = item.get("position") or "Untitled Role"
            company = item.get("company") or "Not specified"
            desc = _strip_html(item.get("description") or "")
            tags = item.get("tags") or []
            job_url = item.get("url") or item.get("apply_url") or ""
            if job_url.startswith("/"):
                job_url = f"https://remoteok.com{job_url}"
            results.append(
                RawOpportunity(
                    title=title,
                    organization=company,
                    description=desc[:4000],
                    source_url=job_url,
                    application_url=item.get("apply_url") or job_url,
                    category_hint=_infer_job_category(title, desc, tags),
                    location=item.get("location") or "Remote",
                    is_remote=True,
                    external_id=str(item.get("id") or job_url),
                    required_skills=[str(t) for t in tags[:10]],
                    raw_payload={"id": item.get("id"), "tags": tags},
                )
            )
        return results


class ArxivResearchAdapter(BaseSourceAdapter):
    """Fetches AI/ML/NLP preprints & research topics from arXiv RSS."""

    adapter_key = "arxiv_research"
    source_name = "arXiv CS.AI/LG/CL Feed"
    source_type = "rss_feed"

    async def fetch(
        self,
        config: dict[str, Any],
        timeout: int = 15,
        max_items: int = 15,
    ) -> List[RawOpportunity]:
        url = config.get("url") or "http://export.arxiv.org/rss/cs.AI+cs.LG+cs.CL"
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=DEFAULT_HEADERS)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

        results: List[RawOpportunity] = []
        for entry in feed.entries[:max_items]:
            title = _strip_html(getattr(entry, "title", "arXiv Research Paper"))
            desc = _strip_html(getattr(entry, "summary", ""))
            link = getattr(entry, "link", "")
            author = getattr(entry, "author", None)
            results.append(
                RawOpportunity(
                    title=title,
                    organization="arXiv (AI/ML/NLP Research)",
                    description=desc[:3500],
                    source_url=link,
                    application_url=link,
                    category_hint="research",
                    location="Remote / Academic",
                    is_remote=True,
                    external_id=link,
                    author_name=author,
                    required_skills=["Artificial Intelligence", "Machine Learning", "Python"],
                    raw_payload={"link": link, "author": author},
                )
            )
        return results


class HuggingFacePapersAdapter(BaseSourceAdapter):
    """Fetches daily AI research papers from Hugging Face public API."""

    adapter_key = "huggingface_papers"
    source_name = "Hugging Face Daily Papers"
    source_type = "api"

    async def fetch(
        self,
        config: dict[str, Any],
        timeout: int = 15,
        max_items: int = 15,
    ) -> List[RawOpportunity]:
        url = config.get("url") or "https://huggingface.co/api/daily_papers"
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=DEFAULT_HEADERS)
            resp.raise_for_status()
            data = resp.json()

        results: List[RawOpportunity] = []
        for item in data[:max_items]:
            paper = item.get("paper") or {}
            paper_id = paper.get("id") or ""
            title = paper.get("title") or item.get("title") or "AI Research Paper"
            summary = paper.get("summary") or ""
            link = f"https://huggingface.co/papers/{paper_id}" if paper_id else "https://huggingface.co/papers"
            results.append(
                RawOpportunity(
                    title=title,
                    organization="Hugging Face Research",
                    description=summary[:3500],
                    source_url=link,
                    application_url=link,
                    category_hint="research",
                    location="Remote / Open Research",
                    is_remote=True,
                    external_id=paper_id or link,
                    required_skills=["Generative AI", "Deep Learning", "NLP"],
                    raw_payload={"paper_id": paper_id},
                )
            )
        return results


class GenericRSSAdapter(BaseSourceAdapter):
    """Configurable RSS/Atom adapter for WeWorkRemotely, hackathons, scholarships, or courses."""

    adapter_key = "wwr_feed"
    source_name = "Public RSS/Atom Feed"
    source_type = "rss_feed"

    async def fetch(
        self,
        config: dict[str, Any],
        timeout: int = 15,
        max_items: int = 20,
    ) -> List[RawOpportunity]:
        url = config.get("url")
        if not url:
            return []
        if is_linkedin_url(url):
            raise ValueError("LinkedIn URLs are blocked in automated RSS fetching.")

        category_override = config.get("category_hint")
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=DEFAULT_HEADERS)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

        results: List[RawOpportunity] = []
        for entry in feed.entries[:max_items]:
            raw_title = _strip_html(getattr(entry, "title", "Opportunity"))
            org = "Not specified"
            title = raw_title
            if ":" in raw_title:
                parts = raw_title.split(":", 1)
                if len(parts[0]) < 60:
                    org = parts[0].strip()
                    title = parts[1].strip()
            desc = _strip_html(getattr(entry, "summary", "") or getattr(entry, "description", ""))
            link = getattr(entry, "link", "")
            cat = category_override or _infer_job_category(title, desc)
            results.append(
                RawOpportunity(
                    title=title,
                    organization=org,
                    description=desc[:4000] or title,
                    source_url=link,
                    application_url=link,
                    category_hint=cat,
                    location=config.get("default_location", "Remote"),
                    is_remote=True,
                    external_id=link,
                    raw_payload={"link": link, "feed_url": url},
                )
            )
        return results


ADAPTER_REGISTRY: dict[str, BaseSourceAdapter] = {
    "remotive_jobs": RemotiveAdapter(),
    "arbeitnow_jobs": ArbeitnowAdapter(),
    "remoteok_feed": RemoteOKAdapter(),
    "arxiv_research": ArxivResearchAdapter(),
    "huggingface_papers": HuggingFacePapersAdapter(),
    "wwr_feed": GenericRSSAdapter(),
    "generic_rss": GenericRSSAdapter(),
}


async def process_manual_submission(
    url: str | None,
    raw_text: str | None,
    title_hint: str | None = None,
    organization_hint: str | None = None,
    category_hint: str | None = None,
    timeout: int = 15,
) -> RawOpportunity:
    """
    Safely process a user-submitted public URL or pasted post text.
    Strictly complies with LinkedIn rules: NEVER scrapes LinkedIn URLs;
    when a LinkedIn URL is submitted, analyzes only the user-provided text/hints.
    """
    extracted_text = (raw_text or "").strip()
    page_title = title_hint or ""

    if url and not is_linkedin_url(url):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=DEFAULT_HEADERS)
                if resp.status_code < 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    if not page_title and soup.title and soup.title.string:
                        page_title = soup.title.string.strip()
                    body_text = _strip_html(resp.text)[:4500]
                    if body_text:
                        extracted_text = f"{extracted_text}\n\n{body_text}".strip()
        except Exception as exc:
            logger.warning(f"Could not fetch manual URL {url}: {exc}")

    if url and is_linkedin_url(url) and not extracted_text:
        raise ValueError(
            "LinkedIn scraping is disabled for compliance. Please paste the public post text alongside the LinkedIn URL."
        )

    final_title = page_title or (extracted_text.splitlines()[0][:120] if extracted_text else "Submitted Opportunity")
    final_org = organization_hint or "Not specified"
    final_cat = category_hint or _infer_job_category(final_title, extracted_text)

    return RawOpportunity(
        title=final_title,
        organization=final_org,
        description=extracted_text or final_title,
        source_url=url or "https://manual-submission.local",
        application_url=url,
        category_hint=final_cat,
        location="Not specified",
        evidence_excerpt=extracted_text[:600] if extracted_text else None,
        raw_payload={"manual_url": url, "has_raw_text": bool(raw_text)},
    )

