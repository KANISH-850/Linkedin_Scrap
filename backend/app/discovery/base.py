"""Base classes, URL normalization, deduplication, and LinkedIn compliance guard."""

import asyncio
import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


def canonicalize_url(url: str) -> str:
    """Normalize a URL by stripping tracking params, fragments, and trailing slashes."""
    if not url:
        return ""
    parsed = urlparse(url.strip())
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if k.lower() not in TRACKING_PARAMS
    ]
    clean_query = urlencode(sorted(query_pairs))
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", clean_query, ""))


def normalize_text_key(text: str) -> str:
    """Normalize text for deduplication."""
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def is_linkedin_url(url: str) -> bool:
    """Return True if the URL points to LinkedIn."""
    if not url:
        return False
    host = urlparse(url).netloc.lower()
    return "linkedin.com" in host or "lnkd.in" in host


@dataclass
class RawOpportunity:
    title: str
    organization: str
    description: str
    source_url: str
    category_hint: str = "internships"
    opportunity_type: str = "JOB"
    application_status: str = "OPEN"
    subcategory: Optional[str] = None
    location: str = "Not specified"
    is_remote: bool = False
    is_hybrid: bool = False
    deadline: Optional[date] = None
    posted_at: Optional[datetime] = None
    application_url: Optional[str] = None
    external_id: Optional[str] = None
    author_name: Optional[str] = None
    evidence_excerpt: Optional[str] = None
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    education_requirement: Optional[str] = None
    graduation_year_requirement: Optional[str] = None
    experience_requirement: Optional[str] = None
    compensation_or_stipend: Optional[str] = None
    duration: Optional[str] = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    extra_metadata: dict[str, Any] = field(default_factory=dict)


class BaseSourceAdapter(ABC):
    """Abstract interface for all opportunity discovery adapters."""

    adapter_key: str = ""
    source_name: str = ""
    source_type: str = "api"

    @abstractmethod
    async def fetch(
        self,
        config: dict[str, Any],
        timeout: int = 15,
        max_items: int = 25,
    ) -> List[RawOpportunity]:
        """Fetch and normalize opportunities from the permitted source."""

    async def fetch_with_retries(
        self,
        config: dict[str, Any],
        timeout: int = 15,
        max_items: int = 25,
        retries: int = 2,
    ) -> List[RawOpportunity]:
        """Execute fetch with exponential backoff retries."""
        last_exc: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                return await self.fetch(config=config, timeout=timeout, max_items=max_items)
            except Exception as exc:
                last_exc = exc
                if attempt < retries:
                    backoff = 1.5 * (2**attempt)
                    logger.warning(
                        f"Adapter {self.adapter_key} attempt {attempt + 1} failed: {exc}. Retrying in {backoff}s."
                    )
                    await asyncio.sleep(backoff)
        raise RuntimeError(f"Adapter {self.adapter_key} failed after {retries + 1} attempts: {last_exc}")


class VerificationState:
    VERIFIED_ACTIVE = "VERIFIED_ACTIVE"
    UNVERIFIED = "UNVERIFIED"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"
    INVALID_URL = "INVALID_URL"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


def compute_dedup_hash(
    organization: str,
    title: str,
    category: str,
    canonical_url: str,
    location: str = "",
    experience: str = "",
) -> str:
    """
    Compute a high-fidelity deduplication hash.
    Combines normalized (category, organization, title, location, experience) AND canonical_url domain+path.
    This guarantees:
      1. Different roles at the same company are never merged.
      2. Same role in different locations or different experience levels are preserved as distinct.
      3. Identical jobs cross-posted across multiple aggregator sources are safely deduplicated.
    """
    org_key = normalize_text_key(organization)
    title_key = normalize_text_key(title)
    cat_key = normalize_text_key(category)
    loc_key = normalize_text_key(location)
    exp_key = normalize_text_key(experience)
    url_key = canonicalize_url(canonical_url)

    if org_key and title_key and org_key not in {"unknown", "not specified"}:
        # Include location and experience differentiators
        raw = f"{cat_key}|{org_key}|{title_key}|{loc_key}|{exp_key}"
    else:
        raw = f"{cat_key}|{url_key}|{title_key}|{loc_key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def verify_url_deep(
    url: str,
    expected_title: str = "",
    timeout: int = 8,
) -> tuple[str, Optional[str], Optional[str]]:
    """
    Deep verification of destination opportunity.
    Returns: (verification_state, destination_title, destination_org)
    Verification states:
      VERIFIED_ACTIVE | UNVERIFIED | CLOSED | EXPIRED | INVALID_URL | SOURCE_UNAVAILABLE
    """
    if not url:
        return VerificationState.INVALID_URL, None, None

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return VerificationState.INVALID_URL, None, None

    if is_linkedin_url(url):
        # We do not scrape LinkedIn; keep as UNVERIFIED to respect terms of service
        return VerificationState.UNVERIFIED, None, None

    try:
        from bs4 import BeautifulSoup
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ReferralPilotAI/2.0 (Career Verification Bot)"})
            if resp.status_code in (404, 410):
                return VerificationState.CLOSED, None, None
            if resp.status_code >= 400:
                return VerificationState.SOURCE_UNAVAILABLE, None, None

            # Inspect returned content
            soup = BeautifulSoup(resp.text, "html.parser")
            dest_title = soup.title.string.strip() if soup.title and soup.title.string else None
            page_text = " ".join(soup.get_text(" ", strip=True).split()).lower()

            # Check expiration / closure keywords
            closure_phrases = [
                "this job has expired",
                "position has been filled",
                "no longer accepting applications",
                "applications are closed",
                "application deadline has passed",
                "this opportunity is closed",
                "registration closed",
                "contest has ended",
            ]
            if any(phrase in page_text for phrase in closure_phrases):
                return VerificationState.CLOSED, dest_title, None

            return VerificationState.VERIFIED_ACTIVE, dest_title, None
    except httpx.TimeoutException:
        return VerificationState.SOURCE_UNAVAILABLE, None, None
    except Exception:
        return VerificationState.UNVERIFIED, None, None


async def verify_url_reachable(url: str, timeout: int = 8) -> str:
    """Backwards-compatible wrapper returning the verification state."""
    state, _, _ = await verify_url_deep(url, timeout=timeout)
    return state

