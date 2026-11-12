"""SQLAlchemy 2.0 ORM models for ReferralPilot AI."""

from datetime import date, datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class UserAccount(Base, TimestampMixin):
    __tablename__ = "user_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="Candidate Admin", nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="Candidate", nullable=False)
    education: Mapped[str] = mapped_column(String(255), nullable=False)
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    current_status: Mapped[str] = mapped_column(String(255), nullable=False)
    target_career_positioning: Mapped[str] = mapped_column(String(255), nullable=False)
    career_goal: Mapped[str] = mapped_column(String(255), nullable=False)
    career_interests: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_locations: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resume_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    skills: Mapped[List["Skill"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Skill.id"
    )
    projects: Mapped[List["Project"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Project.id"
    )


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("profile_id", "name", name="uq_skill_profile_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), default="technical", nullable=False)
    proficiency: Mapped[str] = mapped_column(String(50), default="intermediate", nullable=False)

    profile: Mapped["UserProfile"] = relationship(back_populates="skills")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    achievement: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tech_stack: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    profile: Mapped["UserProfile"] = relationship(back_populates="projects")


class DiscoverySource(Base, TimestampMixin):
    __tablename__ = "discovery_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    adapter_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    frequency_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    records_retrieved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_response_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    opportunity_sources: Mapped[List["OpportunitySource"]] = relationship(back_populates="discovery_source")


class DiscoveryRun(Base, TimestampMixin):
    __tablename__ = "discovery_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="running", nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    sources_checked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    opportunities_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_opportunities: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_match_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_json: Mapped[List[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    summary_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lock_key: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)


class Opportunity(Base, TimestampMixin):
    __tablename__ = "opportunities"
    __table_args__ = (
        Index("ix_opp_category_status", "category", "tracking_status"),
        Index("ix_opp_active_deadline", "active_status", "deadline"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    organization: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # referrals | internships | fresher_jobs | hackathons | scholarships | courses | research
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(200), default="Not specified", nullable=False)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_hybrid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    active_status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    # active | closed | expired | unverified
    verification_status: Mapped[str] = mapped_column(String(40), default="unverified", nullable=False)
    # verified | unverified | unreachable

    canonical_url: Mapped[str] = mapped_column(String(700), nullable=False)
    source_url: Mapped[str] = mapped_column(String(700), nullable=False)
    application_url: Mapped[Optional[str]] = mapped_column(String(700), nullable=True)
    dedup_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # Referral-specific
    referral_classification: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    referral_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    referral_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Extracted fields
    required_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    education_requirement: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    graduation_year_requirement: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    experience_requirement: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    compensation_or_stipend: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # AI & Tracking
    ai_status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    tracking_status: Mapped[str] = mapped_column(String(50), default="NEW", nullable=False, index=True)
    is_interested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    personal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    application_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    referral_received_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    sources: Mapped[List["OpportunitySource"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    evidences: Mapped[List["OpportunityEvidence"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    score: Mapped[Optional["OpportunityScore"]] = relationship(
        back_populates="opportunity", uselist=False, cascade="all, delete-orphan"
    )
    eligibility: Mapped[Optional["EligibilityAssessment"]] = relationship(
        back_populates="opportunity", uselist=False, cascade="all, delete-orphan"
    )
    contacts: Mapped[List["Contact"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    interactions: Mapped[List["Interaction"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    drafts: Mapped[List["MessageDraft"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    applications: Mapped[List["Application"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    follow_ups: Mapped[List["FollowUp"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )
    status_history: Mapped[List["OpportunityStatusHistory"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan", order_by="OpportunityStatusHistory.changed_at.desc()"
    )


class OpportunitySource(Base, TimestampMixin):
    __tablename__ = "opportunity_sources"
    __table_args__ = (UniqueConstraint("opportunity_id", "discovery_source_id", name="uq_opp_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    discovery_source_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("discovery_sources.id", ondelete="SET NULL"), nullable=True
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    raw_url: Mapped[str] = mapped_column(String(700), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="sources")
    discovery_source: Mapped[Optional["DiscoverySource"]] = relationship(back_populates="opportunity_sources")


class OpportunityEvidence(Base, TimestampMixin):
    __tablename__ = "opportunity_evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_url: Mapped[str] = mapped_column(String(700), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="evidences")


class OpportunityScore(Base, TimestampMixin):
    __tablename__ = "opportunity_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    skill_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    eligibility_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    location_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    referral_freshness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(255), nullable=False)
    scoring_model: Mapped[str] = mapped_column(String(80), default="job_internship", nullable=False)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="score")


class EligibilityAssessment(Base, TimestampMixin):
    __tablename__ = "eligibility_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    # Eligible | Likely eligible — verify missing information | Potentially eligible | Not eligible | Insufficient information
    matched_requirements: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    missing_requirements: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    disqualifying_requirements: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    verification_questions: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="eligibility")


class Contact(Base, TimestampMixin):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    profile_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    opportunity: Mapped[Optional["Opportunity"]] = relationship(back_populates="contacts")
    interactions: Mapped[List["Interaction"]] = relationship(back_populates="contact")


class Interaction(Base, TimestampMixin):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=True
    )
    contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    interaction_type: Mapped[str] = mapped_column(String(60), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), default="inbound", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    recommended_next_step: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    opportunity: Mapped[Optional["Opportunity"]] = relationship(back_populates="interactions")
    contact: Mapped[Optional["Contact"]] = relationship(back_populates="interactions")


class MessageDraft(Base, TimestampMixin):
    __tablename__ = "message_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    draft_type: Mapped[str] = mapped_column(String(60), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="drafts")


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(60), default="APPLIED", nullable=False)
    portal_url: Mapped[Optional[str]] = mapped_column(String(700), nullable=True)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resume_version: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="applications")


class FollowUp(Base, TimestampMixin):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="follow_ups")


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True
    )
    discovery_run_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("discovery_runs.id", ondelete="SET NULL"), nullable=True
    )
    channel: Mapped[str] = mapped_column(String(40), default="telegram", nullable=False)
    notification_type: Mapped[str] = mapped_column(String(60), nullable=False)
    dedup_key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class UserSetting(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class TelegramUpdateLog(Base):
    __tablename__ = "telegram_update_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    update_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    chat_id: Mapped[str] = mapped_column(String(64), nullable=False)
    command: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="processed", nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class OpportunityStatusHistory(Base):
    __tablename__ = "opportunity_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    from_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    opportunity: Mapped["Opportunity"] = relationship(back_populates="status_history")

