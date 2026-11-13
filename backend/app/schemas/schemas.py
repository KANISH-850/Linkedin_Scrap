"""Pydantic v2 request and response schemas for ReferralPilot AI."""

from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Auth ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class SetupAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(default="Candidate Admin", min_length=2, max_length=150)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: str
    full_name: str


class UserAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool


# --- Profile, Skills, Projects ---
class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="technical", max_length=80)
    proficiency: str = Field(default="intermediate", max_length=50)


class SkillOut(SkillIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProjectIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    achievement: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    url: Optional[str] = Field(default=None, max_length=512)


class ProjectOut(ProjectIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    education: str
    institution: str
    location: str
    graduation_year: int
    current_status: str
    target_career_positioning: str
    career_goal: str
    career_interests: List[str]
    preferred_locations: List[str]
    cgpa: Optional[float] = None
    resume_summary: Optional[str] = None
    skills: List[SkillOut] = Field(default_factory=list)
    projects: List[ProjectOut] = Field(default_factory=list)
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    education: Optional[str] = Field(default=None, min_length=1, max_length=255)
    institution: Optional[str] = Field(default=None, min_length=1, max_length=255)
    location: Optional[str] = Field(default=None, min_length=1, max_length=255)
    graduation_year: Optional[int] = Field(default=None, ge=2020, le=2035)
    current_status: Optional[str] = Field(default=None, min_length=1, max_length=255)
    target_career_positioning: Optional[str] = Field(default=None, min_length=1, max_length=255)
    career_goal: Optional[str] = Field(default=None, min_length=1, max_length=255)
    career_interests: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    cgpa: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    resume_summary: Optional[str] = None
    skills: Optional[List[SkillIn]] = None
    projects: Optional[List[ProjectIn]] = None


# --- Opportunity & Analysis ---
class OpportunityScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    overall_score: float
    skill_score: float
    eligibility_score: float
    relevance_score: float
    location_score: float
    referral_freshness_score: float
    explanation: str
    recommended_action: str
    scoring_model: str
    scored_at: datetime


class EligibilityAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    matched_requirements: List[str]
    missing_requirements: List[str]
    disqualifying_requirements: List[str]
    verification_questions: List[str]
    summary: str
    assessed_at: datetime


class OpportunityEvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    evidence_type: str
    source_url: str
    excerpt: str
    author_name: Optional[str] = None
    extracted_at: datetime


class MessageDraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    opportunity_id: int
    draft_type: str
    subject: Optional[str] = None
    body: str
    created_at: datetime


class OpportunityStatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    from_status: Optional[str] = None
    to_status: str
    note: Optional[str] = None
    changed_at: datetime


class OpportunitySummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    organization: str
    category: str
    subcategory: Optional[str] = None
    opportunity_type: str = "JOB"
    application_status: str = "OPEN"
    description: str
    location: str
    is_remote: bool
    is_hybrid: bool
    deadline: Optional[date] = None
    discovered_at: datetime
    last_verified_at: Optional[datetime] = None
    active_status: str
    verification_status: str
    source_url: str
    application_url: Optional[str] = None
    referral_classification: Optional[str] = None
    referral_confidence: Optional[float] = None
    required_skills: List[str]
    preferred_skills: List[str]
    compensation_or_stipend: Optional[str] = None
    ai_status: str
    tracking_status: str
    is_interested: bool
    follow_up_date: Optional[date] = None
    next_action: Optional[str] = None
    score: Optional[OpportunityScoreOut] = None
    eligibility: Optional[EligibilityAssessmentOut] = None


class OpportunityDetailOut(OpportunitySummaryOut):
    canonical_url: str
    referral_instructions: Optional[str] = None
    education_requirement: Optional[str] = None
    graduation_year_requirement: Optional[str] = None
    experience_requirement: Optional[str] = None
    duration: Optional[str] = None
    extra_metadata: dict[str, Any] = Field(default_factory=dict)
    personal_notes: Optional[str] = None
    application_date: Optional[datetime] = None
    referral_received_date: Optional[datetime] = None
    evidences: List[OpportunityEvidenceOut] = Field(default_factory=list)
    drafts: List[MessageDraftOut] = Field(default_factory=list)
    status_history: List[OpportunityStatusHistoryOut] = Field(default_factory=list)


class PaginatedOpportunities(BaseModel):
    items: List[OpportunitySummaryOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class OpportunityStatusUpdate(BaseModel):
    tracking_status: Optional[str] = None
    is_interested: Optional[bool] = None
    personal_notes: Optional[str] = None
    next_action: Optional[str] = None
    follow_up_date: Optional[date] = None
    referral_received_date: Optional[datetime] = None
    note: Optional[str] = None


class DraftMessageRequest(BaseModel):
    draft_type: str = Field(
        description="connection_request | referral_request | recruiter_outreach | follow_up | thank_you | application_email | reply_response"
    )
    contact_name: Optional[str] = None
    custom_context: Optional[str] = None


class FollowUpCreate(BaseModel):
    due_date: date
    notes: Optional[str] = None


class FollowUpUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    opportunity_id: int
    due_date: date
    status: str
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    opportunity_title: Optional[str] = None
    organization: Optional[str] = None


class ApplicationCreate(BaseModel):
    opportunity_id: int
    status: str = "APPLIED"
    portal_url: Optional[str] = None
    resume_version: Optional[str] = None
    notes: Optional[str] = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    opportunity_id: int
    status: str
    portal_url: Optional[str] = None
    applied_at: Optional[datetime] = None
    resume_version: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    opportunity_title: Optional[str] = None
    organization: Optional[str] = None


# --- Reply Intelligence ---
class ReplyAnalyzeRequest(BaseModel):
    opportunity_id: Optional[int] = None
    reply_text: str = Field(min_length=3)
    sender_name: Optional[str] = None


class ReplyAnalyzeResponse(BaseModel):
    classification: str
    explanation: str
    recommended_next_step: str
    suggested_response: str
    suggested_follow_up_date: Optional[date] = None


# --- Discovery Sources & Runs ---
class DiscoverySourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    adapter_key: str
    source_type: str
    enabled: bool
    frequency_hours: int
    config_json: dict[str, Any]
    last_run_at: Optional[datetime] = None
    last_status: Optional[str] = None
    last_error: Optional[str] = None
    records_retrieved: Optional[int] = 0
    valid_records: Optional[int] = 0
    duplicate_records: Optional[int] = 0
    new_records: Optional[int] = 0
    avg_response_time_ms: Optional[int] = 0


class DiscoverySourceUpdate(BaseModel):
    enabled: Optional[bool] = None
    frequency_hours: Optional[int] = Field(default=None, ge=1, le=168)
    config_json: Optional[dict[str, Any]] = None


class ManualSubmissionRequest(BaseModel):
    url: Optional[str] = None
    raw_text: Optional[str] = None
    title_hint: Optional[str] = None
    organization_hint: Optional[str] = None
    category_hint: Optional[str] = None


class DiscoveryRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    trigger_type: str
    sources_checked: int
    sources_failed: int
    opportunities_discovered: int
    new_opportunities: int
    high_match_count: int
    errors_json: List[dict[str, Any]]
    summary_text: Optional[str] = None


# --- Dashboard & Settings ---
class DashboardSummaryOut(BaseModel):
    new_opportunities: int
    high_match_opportunities: int
    referrals_in_progress: int
    applications_submitted: int
    replies_received: int
    upcoming_deadlines: int
    follow_ups_due: int
    total_opportunities: int
    active_vacancies: int = 0
    research_papers: int = 0
    closed_opportunities: int = 0
    latest_run: Optional[DiscoveryRunOut] = None


class AnalyticsSeriesPoint(BaseModel):
    label: str
    count: int


class DashboardAnalyticsOut(BaseModel):
    discovered_over_time: List[AnalyticsSeriesPoint]
    by_category: List[AnalyticsSeriesPoint]
    application_pipeline: List[AnalyticsSeriesPoint]
    score_distribution: List[AnalyticsSeriesPoint]
    outreach_status: List[AnalyticsSeriesPoint]
    by_opportunity_type: List[AnalyticsSeriesPoint] = []
    by_application_status: List[AnalyticsSeriesPoint] = []


class ScoringWeightsUpdate(BaseModel):
    skill_match: float = Field(ge=0.0, le=1.0)
    eligibility_match: float = Field(ge=0.0, le=1.0)
    role_relevance: float = Field(ge=0.0, le=1.0)
    location_preference: float = Field(ge=0.0, le=1.0)
    referral_freshness: float = Field(ge=0.0, le=1.0)
    high_match_threshold: int = Field(default=75, ge=40, le=95)

