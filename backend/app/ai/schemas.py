"""Pydantic schemas for AI output validation and base LLM interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field


class AIExtractionResult(BaseModel):
    category: str = Field(
        description="referrals | internships | fresher_jobs | hackathons | scholarships | courses | research"
    )
    subcategory: Optional[str] = None
    role_or_title: str
    organization: str
    location: str = "Not specified"
    is_remote: bool = False
    is_hybrid: bool = False
    deadline: Optional[str] = Field(
        default=None, description="ISO YYYY-MM-DD date if explicitly stated, otherwise null. Never fabricate."
    )
    referral_classification: Optional[str] = Field(
        default=None,
        description="confirmed_referral_offer | explicit_referral_request | hiring_with_possible_referral | general_job_announcement | unclear_evidence",
    )
    referral_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    referral_instructions: Optional[str] = None
    referral_evidence_excerpt: Optional[str] = None
    recruiter_or_author_name: Optional[str] = None

    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    education_requirement: Optional[str] = None
    graduation_year_requirement: Optional[str] = None
    experience_requirement: Optional[str] = None
    compensation_or_stipend: Optional[str] = None
    duration: Optional[str] = None


class AIEligibilityResult(BaseModel):
    status: str = Field(
        description="Eligible | Likely eligible — verify missing information | Potentially eligible | Not eligible | Insufficient information"
    )
    matched_requirements: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    disqualifying_requirements: List[str] = Field(default_factory=list)
    verification_questions: List[str] = Field(default_factory=list)
    summary: str


class AIScoringResult(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    skill_score: float = Field(ge=0.0, le=100.0)
    eligibility_score: float = Field(ge=0.0, le=100.0)
    relevance_score: float = Field(ge=0.0, le=100.0)
    location_score: float = Field(ge=0.0, le=100.0)
    referral_freshness_score: float = Field(ge=0.0, le=100.0)
    explanation: str
    recommended_action: str


class AIDraftMessageResult(BaseModel):
    draft_type: str
    subject: Optional[str] = None
    body: str


class AIReplyAnalysisResult(BaseModel):
    classification: str = Field(
        description="Positive response | Referral possible | Resume requested | Apply through official portal | Additional information requested | Follow-up needed | Not interested | Rejection | Unclear response"
    )
    explanation: str
    recommended_next_step: str
    suggested_response: str
    suggested_follow_up_days: Optional[int] = None


class BaseLLMClient(ABC):
    """Abstract interface for LLM provider implementations."""

    @abstractmethod
    async def extract_and_classify(self, text: str, title: str, context: dict) -> AIExtractionResult:
        pass

    @abstractmethod
    async def evaluate_eligibility_and_score(
        self, candidate_profile: dict, opportunity_data: dict, weights: dict
    ) -> tuple[AIEligibilityResult, AIScoringResult]:
        pass

    @abstractmethod
    async def draft_message(
        self, candidate_profile: dict, opportunity_data: dict, draft_type: str, custom_context: str | None = None
    ) -> AIDraftMessageResult:
        pass

    @abstractmethod
    async def analyze_reply(
        self, reply_text: str, opportunity_data: dict | None, candidate_profile: dict
    ) -> AIReplyAnalysisResult:
        pass

