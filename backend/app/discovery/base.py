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


def compute_dedup_hash(organization: str, title: str, category: str, canonical_url: str) -> str:
    """
    Compute a stable deduplication hash.
    Uses normalized (organization, title, category) AND canonical_url domain+path
    so different roles at the same company are never accidentally merged.
    """
    org_key = normalize_text_key(organization)
    title_key = normalize_text_key(title)
    cat_key = normalize_text_key(category)
    url_key = canonicalize_url(canonical_url)
    # If organization & title are both known and non-generic, key primarily on org + title + category
    if org_key and title_key and org_key not in {"unknown", "not specified"}:
        raw = f"{cat_key}|{org_key}|{title_key}"
    else:
        raw = f"{cat_key}|{url_key}|{title_key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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


async def verify_url_reachable(url: str, timeout: int = 8) -> str:
    """
    Verify whether an official/source URL is reachable.
    Never scrapes LinkedIn; returns 'unverified' for LinkedIn URLs.
    """
    if not url:
        return "unverified"
    if is_linkedin_url(url):
        return "unverified"
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.head(url, headers={"User-Agent": "ReferralPilotAI/1.0"})
            if resp.status_code < 400:
                return "verified"
            if resp.status_code in (403, 405):
                # Some career portals block HEAD requests; try lightweight GET
                resp_get = await client.get(url, headers={"User-Agent": "ReferralPilotAI/1.0"})
                return "verified" if resp_get.status_code < 400 else "unreachable"
            return "unreachable"
    except Exception:
        return "unverified"

