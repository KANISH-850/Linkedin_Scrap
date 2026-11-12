from app.discovery.base import (
    BaseSourceAdapter,
    RawOpportunity,
    canonicalize_url,
    compute_dedup_hash,
    is_linkedin_url,
    verify_url_reachable,
)
from app.discovery.adapters import (
    ADAPTER_REGISTRY,
    ArbeitnowAdapter,
    ArxivResearchAdapter,
    GenericRSSAdapter,
    HuggingFacePapersAdapter,
    RemotiveAdapter,
    RemoteOKAdapter,
    process_manual_submission,
)

__all__ = [
    "BaseSourceAdapter",
    "RawOpportunity",
    "canonicalize_url",
    "compute_dedup_hash",
    "is_linkedin_url",
    "verify_url_reachable",
    "ADAPTER_REGISTRY",
    "RemotiveAdapter",
    "ArbeitnowAdapter",
    "RemoteOKAdapter",
    "ArxivResearchAdapter",
    "HuggingFacePapersAdapter",
    "GenericRSSAdapter",
    "process_manual_submission",
]

