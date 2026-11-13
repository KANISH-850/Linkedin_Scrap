"""Core FastAPI router implementing all ReferralPilot AI endpoints."""

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.ai.service import ai_service
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    rate_limit_discovery,
    rate_limit_login,
    verify_password,
)
from app.database.session import get_db
from app.discovery.adapters import process_manual_submission
from app.models.models import (
    Application,
    DiscoveryRun,
    DiscoverySource,
    EligibilityAssessment,
    FollowUp,
    Interaction,
    MessageDraft,
    Opportunity,
    OpportunityScore,
    OpportunityStatusHistory,
    Project,
    Skill,
    UserAccount,
    UserProfile,
    UserSetting,
)
from app.schemas.schemas import (
    AnalyticsSeriesPoint,
    ApplicationCreate,
    ApplicationOut,
    DashboardAnalyticsOut,
    DashboardSummaryOut,
    DiscoveryRunOut,
    DiscoverySourceOut,
    DiscoverySourceUpdate,
    DraftMessageRequest,
    FollowUpCreate,
    FollowUpOut,
    FollowUpUpdate,
    LoginRequest,
    ManualSubmissionRequest,
    MessageDraftOut,
    OpportunityDetailOut,
    OpportunityStatusUpdate,
    OpportunitySummaryOut,
    PaginatedOpportunities,
    ReplyAnalyzeRequest,
    ReplyAnalyzeResponse,
    ScoringWeightsUpdate,
    SetupAdminRequest,
    TokenResponse,
    UserAccountOut,
    UserProfileOut,
    UserProfileUpdate,
)
from app.services.discovery_service import discovery_engine
from app.telegram.service import telegram_service

router = APIRouter()


# --- Auth Endpoints ---
@router.post("/api/auth/setup", response_model=TokenResponse, tags=["Auth"])
def setup_initial_admin(payload: SetupAdminRequest, db: Session = Depends(get_db)):
    """Create the initial admin account only if no accounts exist."""
    existing_count = db.query(UserAccount).count()
    if existing_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Initial admin account already exists.",
        )
    user = UserAccount(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.email, role=user.role)
    return TokenResponse(access_token=token, user_email=user.email, full_name=user.full_name)


@router.post("/api/auth/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_login)], tags=["Auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserAccount).filter(UserAccount.email == payload.email, UserAccount.is_active.is_(True)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    token = create_access_token(subject=user.email, role=user.role)
    return TokenResponse(access_token=token, user_email=user.email, full_name=user.full_name)


@router.get("/api/auth/me", response_model=UserAccountOut, tags=["Auth"])
def get_me(current_user: UserAccount = Depends(get_current_user)):
    return current_user


# --- Candidate Profile Endpoints ---
@router.get("/api/profile", response_model=UserProfileOut, tags=["Profile"])
def get_profile(db: Session = Depends(get_db), _: UserAccount = Depends(get_current_user)):
    profile = db.query(UserProfile).options(joinedload(UserProfile.skills), joinedload(UserProfile.projects)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    return profile


@router.put("/api/profile", response_model=UserProfileOut, tags=["Profile"])
def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")

    update_data = payload.model_dump(exclude_unset=True, exclude={"skills", "projects"})
    for field, value in update_data.items():
        setattr(profile, field, value)

    if payload.skills is not None:
        db.query(Skill).filter(Skill.profile_id == profile.id).delete()
        for sk in payload.skills:
            db.add(Skill(profile_id=profile.id, **sk.model_dump()))

    if payload.projects is not None:
        db.query(Project).filter(Project.profile_id == profile.id).delete()
        for pr in payload.projects:
            db.add(Project(profile_id=profile.id, **pr.model_dump()))

    db.commit()
    db.refresh(profile)
    return db.query(UserProfile).options(joinedload(UserProfile.skills), joinedload(UserProfile.projects)).first()


# --- Opportunities Endpoints ---
@router.get("/api/opportunities", response_model=PaginatedOpportunities, tags=["Opportunities"])
def list_opportunities(
    category: Optional[str] = None,
    min_score: Optional[float] = Query(default=None, ge=0, le=100),
    eligibility: Optional[str] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    active_status: Optional[str] = None,
    verification_status: Optional[str] = None,
    tracking_status: Optional[str] = None,
    referral_classification: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "score_desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    query = db.query(Opportunity).options(
        joinedload(Opportunity.score),
        joinedload(Opportunity.eligibility),
    )

    if category:
        query = query.filter(Opportunity.category == category)
    if active_status:
        query = query.filter(Opportunity.active_status == active_status)
    if verification_status:
        query = query.filter(Opportunity.verification_status == verification_status)
    if tracking_status:
        query = query.filter(Opportunity.tracking_status == tracking_status)
    if referral_classification:
        query = query.filter(Opportunity.referral_classification == referral_classification)
    if location:
        query = query.filter(Opportunity.location.ilike(f"%{location}%"))
    if company:
        query = query.filter(Opportunity.organization.ilike(f"%{company}%"))
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Opportunity.title.ilike(pattern))
            | (Opportunity.organization.ilike(pattern))
            | (Opportunity.description.ilike(pattern))
        )

    if min_score is not None or sort_by in ("score_desc", "score_asc"):
        query = query.outerjoin(OpportunityScore)
        if min_score is not None:
            query = query.filter(OpportunityScore.overall_score >= min_score)

    if eligibility:
        query = query.outerjoin(EligibilityAssessment).filter(EligibilityAssessment.status == eligibility)

    total = query.count()

    if sort_by == "score_desc":
        query = query.order_by(OpportunityScore.overall_score.desc().nullslast(), Opportunity.discovered_at.desc())
    elif sort_by == "score_asc":
        query = query.order_by(OpportunityScore.overall_score.asc().nullslast())
    elif sort_by == "deadline_asc":
        query = query.order_by(Opportunity.deadline.asc().nullslast())
    else:
        query = query.order_by(Opportunity.discovered_at.desc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = max((total + page_size - 1) // page_size, 1)

    return PaginatedOpportunities(
        items=[OpportunitySummaryOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/api/opportunities/{opp_id}", response_model=OpportunityDetailOut, tags=["Opportunities"])
def get_opportunity(opp_id: int, db: Session = Depends(get_db), _: UserAccount = Depends(get_current_user)):
    opp = (
        db.query(Opportunity)
        .options(
            joinedload(Opportunity.score),
            joinedload(Opportunity.eligibility),
            joinedload(Opportunity.evidences),
            joinedload(Opportunity.drafts),
            joinedload(Opportunity.status_history),
        )
        .filter(Opportunity.id == opp_id)
        .first()
    )
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    return opp


@router.patch("/api/opportunities/{opp_id}/status", response_model=OpportunityDetailOut, tags=["Opportunities"])
def update_opportunity_status(
    opp_id: int,
    payload: OpportunityStatusUpdate,
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    if payload.tracking_status and payload.tracking_status != opp.tracking_status:
        db.add(
            OpportunityStatusHistory(
                opportunity_id=opp.id,
                from_status=opp.tracking_status,
                to_status=payload.tracking_status,
                note=payload.note,
            )
        )
        opp.tracking_status = payload.tracking_status
        if payload.tracking_status == "APPLIED" and not opp.application_date:
            opp.application_date = datetime.now(timezone.utc)
        if payload.tracking_status == "REFERRAL_RECEIVED" and not opp.referral_received_date:
            opp.referral_received_date = datetime.now(timezone.utc)

    if payload.is_interested is not None:
        opp.is_interested = payload.is_interested
    if payload.personal_notes is not None:
        opp.personal_notes = payload.personal_notes
    if payload.next_action is not None:
        opp.next_action = payload.next_action
    if payload.follow_up_date is not None:
        opp.follow_up_date = payload.follow_up_date
    if payload.referral_received_date is not None:
        opp.referral_received_date = payload.referral_received_date

    db.commit()
    return get_opportunity(opp_id, db)


@router.post("/api/opportunities/{opp_id}/draft-message", response_model=MessageDraftOut, tags=["Opportunities"])
async def draft_opportunity_message(
    opp_id: int,
    payload: DraftMessageRequest,
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    profile = db.query(UserProfile).first()
    profile_dict = {
        "full_name": profile.full_name if profile else "Kanish K",
        "institution": profile.institution if profile else "Bannari Amman Institute of Technology",
        "graduation_year": profile.graduation_year if profile else 2028,
        "skills": [s.name for s in (profile.skills if profile else [])],
    }
    opp_dict = {
        "title": opp.title,
        "organization": opp.organization,
        "contact_name": payload.contact_name,
    }
    result = await ai_service.draft_message(profile_dict, opp_dict, payload.draft_type, payload.custom_context)

    draft = MessageDraft(
        opportunity_id=opp.id,
        draft_type=result.draft_type,
        subject=result.subject,
        body=result.body,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/api/opportunities/{opp_id}/follow-up", response_model=FollowUpOut, tags=["Follow-ups"])
def create_follow_up(
    opp_id: int,
    payload: FollowUpCreate,
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    fup = FollowUp(opportunity_id=opp.id, due_date=payload.due_date, notes=payload.notes, status="pending")
    opp.follow_up_date = payload.due_date
    db.add(fup)
    db.commit()
    db.refresh(fup)
    return FollowUpOut(
        **{
            "id": fup.id,
            "opportunity_id": fup.opportunity_id,
            "due_date": fup.due_date,
            "status": fup.status,
            "notes": fup.notes,
            "completed_at": fup.completed_at,
            "created_at": fup.created_at,
            "opportunity_title": opp.title,
            "organization": opp.organization,
        }
    )


# --- Follow-ups & Applications ---
@router.get("/api/follow-ups", response_model=List[FollowUpOut], tags=["Follow-ups"])
def list_follow_ups(db: Session = Depends(get_db), _: UserAccount = Depends(get_current_user)):
    rows = db.query(FollowUp).order_by(FollowUp.status.asc(), FollowUp.due_date.asc()).all()
    out = []
    for f in rows:
        opp = db.query(Opportunity).filter(Opportunity.id == f.opportunity_id).first()
        out.append(
            FollowUpOut(
                id=f.id,
                opportunity_id=f.opportunity_id,
                due_date=f.due_date,
                status=f.status,
                notes=f.notes,
                completed_at=f.completed_at,
                created_at=f.created_at,
                opportunity_title=opp.title if opp else None,
                organization=opp.organization if opp else None,
            )
        )
    return out


@router.patch("/api/follow-ups/{fup_id}", response_model=FollowUpOut, tags=["Follow-ups"])
def update_follow_up(
    fup_id: int,
    payload: FollowUpUpdate,
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    f = db.query(FollowUp).filter(FollowUp.id == fup_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Follow-up not found.")
    if payload.status:
        f.status = payload.status
        if payload.status == "completed":
            f.completed_at = datetime.now(timezone.utc)
    if payload.due_date:
        f.due_date = payload.due_date
    if payload.notes is not None:
        f.notes = payload.notes
    db.commit()
    db.refresh(f)
    opp = db.query(Opportunity).filter(Opportunity.id == f.opportunity_id).first()
    return FollowUpOut(
        id=f.id,
        opportunity_id=f.opportunity_id,
        due_date=f.due_date,
        status=f.status,
        notes=f.notes,
        completed_at=f.completed_at,
        created_at=f.created_at,
        opportunity_title=opp.title if opp else None,
        organization=opp.organization if opp else None,
    )


@router.get("/api/applications", response_model=List[ApplicationOut], tags=["Applications"])
def list_applications(db: Session = Depends(get_db), _: UserAccount = Depends(get_current_user)):
    rows = db.query(Application).order_by(Application.created_at.desc()).all()
    out = []
    for a in rows:
        opp = db.query(Opportunity).filter(Opportunity.id == a.opportunity_id).first()
        out.append(
            ApplicationOut(
                id=a.id,
                opportunity_id=a.opportunity_id,
                status=a.status,
                portal_url=a.portal_url,
                applied_at=a.applied_at,
                resume_version=a.resume_version,
                notes=a.notes,
                created_at=a.created_at,
                opportunity_title=opp.title if opp else None,
                organization=opp.organization if opp else None,
            )
        )
    return out


@router.post("/api/applications", response_model=ApplicationOut, tags=["Applications"])
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    opp = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    now = datetime.now(timezone.utc)
    app_rec = Application(
        opportunity_id=opp.id,
        status=payload.status,
        portal_url=payload.portal_url or opp.application_url or opp.source_url,
        applied_at=now,
        resume_version=payload.resume_version,
        notes=payload.notes,
    )
    if opp.tracking_status != payload.status:
        db.add(
            OpportunityStatusHistory(
                opportunity_id=opp.id,
                from_status=opp.tracking_status,
                to_status=payload.status,
                note="Application recorded",
            )
        )
        opp.tracking_status = payload.status
        opp.application_date = now

    db.add(app_rec)
    db.commit()
    db.refresh(app_rec)
    return ApplicationOut(
        id=app_rec.id,
        opportunity_id=app_rec.opportunity_id,
        status=app_rec.status,
        portal_url=app_rec.portal_url,
        applied_at=app_rec.applied_at,
        resume_version=app_rec.resume_version,
        notes=app_rec.notes,
        created_at=app_rec.created_at,
        opportunity_title=opp.title,
        organization=opp.organization,
    )


# --- Dashboard Summary & Analytics ---
@router.get("/api/dashboard/summary", response_model=DashboardSummaryOut, tags=["Dashboard"])
def get_dashboard_summary(db: Session = Depends(get_db), _: UserAccount = Depends(get_current_user)):
    settings = get_settings()
    today = date.today()
    soon = today + timedelta(days=7)

    # Exclude research papers and closed opportunities from active/new counts
    new_opps = (
        db.query(Opportunity)
        .filter(
            Opportunity.tracking_status == "NEW",
            Opportunity.opportunity_type != "RESEARCH_PAPER",
            Opportunity.application_status == "OPEN",
        )
        .count()
    )
    high_match = (
        db.query(OpportunityScore)
        .join(Opportunity, OpportunityScore.opportunity_id == Opportunity.id)
        .filter(
            OpportunityScore.overall_score >= settings.high_match_threshold,
            Opportunity.opportunity_type != "RESEARCH_PAPER",
            Opportunity.application_status == "OPEN",
        )
        .count()
    )
    referrals_in_prog = (
        db.query(Opportunity)
        .filter(Opportunity.tracking_status.in_(["CONNECTION_PENDING", "CONNECTED", "REPLY_RECEIVED", "REFERRAL_RECEIVED"]))
        .count()
    )
    apps_submitted = db.query(Application).count()
    replies_rec = db.query(Interaction).filter(Interaction.direction == "inbound").count()
    deadlines = (
        db.query(Opportunity)
        .filter(Opportunity.deadline.isnot(None), Opportunity.deadline >= today, Opportunity.deadline <= soon)
        .count()
    )
    fups_due = db.query(FollowUp).filter(FollowUp.status == "pending", FollowUp.due_date <= today).count()
    total_opps = db.query(Opportunity).count()
    
    active_vacancies = (
        db.query(Opportunity)
        .filter(
            Opportunity.opportunity_type.in_(["JOB", "INTERNSHIP"]),
            Opportunity.application_status == "OPEN",
        )
        .count()
    )
    research_papers = (
        db.query(Opportunity)
        .filter(Opportunity.opportunity_type == "RESEARCH_PAPER")
        .count()
    )
    closed_opps = (
        db.query(Opportunity)
        .filter(Opportunity.application_status == "CLOSED")
        .count()
    )
    latest_run = db.query(DiscoveryRun).order_by(DiscoveryRun.started_at.desc()).first()

    return DashboardSummaryOut(
        new_opportunities=new_opps,
        high_match_opportunities=high_match,
        referrals_in_progress=referrals_in_prog,
        applications_submitted=apps_submitted,
        replies_received=replies_rec,
        upcoming_deadlines=deadlines,
        follow_ups_due=fups_due,
        total_opportunities=total_opps,
        active_vacancies=active_vacancies,
        research_papers=research_papers,
        closed_opportunities=closed_opps,
        latest_run=DiscoveryRunOut.model_validate(latest_run) if latest_run else None,
    )


@router.get("/api/dashboard/analytics", response_model=DashboardAnalyticsOut, tags=["Dashboard"])
def get_dashboard_analytics(db: Session = Depends(get_db), _: UserAccount = Depends(get_current_user)):
    cat_rows = db.query(Opportunity.category, func.count(Opportunity.id)).group_by(Opportunity.category).all()
    by_category = [AnalyticsSeriesPoint(label=r[0] or "other", count=r[1]) for r in cat_rows]

    opp_type_rows = (
        db.query(Opportunity.opportunity_type, func.count(Opportunity.id))
        .group_by(Opportunity.opportunity_type)
        .all()
    )
    by_opportunity_type = [AnalyticsSeriesPoint(label=r[0] or "OTHER", count=r[1]) for r in opp_type_rows]

    app_status_rows = (
        db.query(Opportunity.application_status, func.count(Opportunity.id))
        .group_by(Opportunity.application_status)
        .all()
    )
    by_application_status = [AnalyticsSeriesPoint(label=r[0] or "OPEN", count=r[1]) for r in app_status_rows]

    status_rows = (
        db.query(Opportunity.tracking_status, func.count(Opportunity.id)).group_by(Opportunity.tracking_status).all()
    )
    application_pipeline = [AnalyticsSeriesPoint(label=r[0] or "unknown", count=r[1]) for r in status_rows]

    # Score distribution buckets
    scores = [s[0] for s in db.query(OpportunityScore.overall_score).all()]
    buckets = {"90-100": 0, "75-89": 0, "60-74": 0, "<60": 0}
    for sc in scores:
        if sc >= 90:
            buckets["90-100"] += 1
        elif sc >= 75:
            buckets["75-89"] += 1
        elif sc >= 60:
            buckets["60-74"] += 1
        else:
            buckets["<60"] += 1
    score_distribution = [AnalyticsSeriesPoint(label=k, count=v) for k, v in buckets.items()]

    # Discovered over last 7 days
    all_opps = db.query(Opportunity.discovered_at).all()
    day_counts: dict[str, int] = {}
    for i in range(6, -1, -1):
        d_str = (date.today() - timedelta(days=i)).isoformat()
        day_counts[d_str] = 0
    for (dt,) in all_opps:
        if dt:
            d_str = dt.date().isoformat()
            if d_str in day_counts:
                day_counts[d_str] += 1
    discovered_over_time = [AnalyticsSeriesPoint(label=k, count=v) for k, v in day_counts.items()]

    outreach_statuses = ["CONNECTION_PENDING", "CONNECTED", "REPLY_RECEIVED", "REFERRAL_RECEIVED"]
    outreach_rows = (
        db.query(Opportunity.tracking_status, func.count(Opportunity.id))
        .filter(Opportunity.tracking_status.in_(outreach_statuses))
        .group_by(Opportunity.tracking_status)
        .all()
    )
    outreach_status = [AnalyticsSeriesPoint(label=r[0] or "unknown", count=r[1]) for r in outreach_rows]

    return DashboardAnalyticsOut(
        discovered_over_time=discovered_over_time,
        by_category=by_category,
        application_pipeline=application_pipeline,
        score_distribution=score_distribution,
        outreach_status=outreach_status,
        by_opportunity_type=by_opportunity_type,
        by_application_status=by_application_status,
    )


# --- Sources & Discovery ---
@router.get("/api/sources", response_model=List[DiscoverySourceOut], tags=["Discovery"])
def list_sources(db: Session = Depends(get_db), _: UserAccount = Depends(get_current_user)):
    return db.query(DiscoverySource).order_by(DiscoverySource.id.asc()).all()


@router.patch("/api/sources/{source_id}", response_model=DiscoverySourceOut, tags=["Discovery"])
def update_source(
    source_id: int,
    payload: DiscoverySourceUpdate,
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    src = db.query(DiscoverySource).filter(DiscoverySource.id == source_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="Discovery source not found.")
    if payload.enabled is not None:
        src.enabled = payload.enabled
    if payload.frequency_hours is not None:
        src.frequency_hours = payload.frequency_hours
    if payload.config_json is not None:
        src.config_json = payload.config_json
    db.commit()
    db.refresh(src)
    return src


@router.post("/api/discovery/run", response_model=DiscoveryRunOut, dependencies=[Depends(rate_limit_discovery)], tags=["Discovery"])
async def trigger_discovery_run(
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    run = await discovery_engine.execute_run(db, trigger_type="manual_dashboard")
    return run


@router.post("/api/discovery/submit", response_model=OpportunityDetailOut, tags=["Discovery"])
async def submit_manual_opportunity(
    payload: ManualSubmissionRequest,
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    if not payload.url and not payload.raw_text:
        raise HTTPException(status_code=400, detail="Provide at least a URL or post text.")
    try:
        raw = await process_manual_submission(
            url=payload.url,
            raw_text=payload.raw_text,
            title_hint=payload.title_hint,
            organization_hint=payload.organization_hint,
            category_hint=payload.category_hint,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    profile = db.query(UserProfile).first()
    profile_dict = {
        "graduation_year": profile.graduation_year if profile else 2028,
        "target_career_positioning": profile.target_career_positioning if profile else "AI Engineer",
        "skills": [s.name for s in (profile.skills if profile else [])],
        "full_name": profile.full_name if profile else "Kanish K",
        "institution": profile.institution if profile else "Bannari Amman Institute of Technology",
    }
    weights_setting = db.query(UserSetting).filter(UserSetting.key == "scoring_weights").first()
    weights = weights_setting.value if weights_setting else {}

    src = db.query(DiscoverySource).filter(DiscoverySource.adapter_key == "user_submitted").first()
    _, opp = await discovery_engine._persist_raw_opportunity(
        db, raw, src.id if src else None, profile_dict, weights
    )
    if not opp:
        raise HTTPException(status_code=500, detail="Failed to persist submitted opportunity.")
    return get_opportunity(opp.id, db)


@router.get("/api/discovery/runs", response_model=List[DiscoveryRunOut], tags=["Discovery"])
def list_discovery_runs(db: Session = Depends(get_db), _: UserAccount = Depends(get_current_user)):
    return db.query(DiscoveryRun).order_by(DiscoveryRun.started_at.desc()).limit(30).all()


# --- Reply Intelligence ---
@router.post("/api/replies/analyze", response_model=ReplyAnalyzeResponse, tags=["Replies"])
async def analyze_reply(
    payload: ReplyAnalyzeRequest,
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    opp = None
    opp_dict = None
    if payload.opportunity_id:
        opp = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
        if opp:
            opp_dict = {"title": opp.title, "organization": opp.organization}

    profile = db.query(UserProfile).first()
    profile_dict = {
        "full_name": profile.full_name if profile else "Kanish K",
        "target_career_positioning": profile.target_career_positioning if profile else "AI Engineer",
    }

    analysis = await ai_service.analyze_reply(payload.reply_text, opp_dict, profile_dict)
    follow_up_date = (
        date.today() + timedelta(days=analysis.suggested_follow_up_days)
        if analysis.suggested_follow_up_days
        else None
    )

    if opp:
        db.add(
            Interaction(
                opportunity_id=opp.id,
                interaction_type="reply",
                direction="inbound",
                content=payload.reply_text,
                classification=analysis.classification,
                recommended_next_step=analysis.recommended_next_step,
                suggested_response=analysis.suggested_response,
            )
        )
        db.commit()

    return ReplyAnalyzeResponse(
        classification=analysis.classification,
        explanation=analysis.explanation,
        recommended_next_step=analysis.recommended_next_step,
        suggested_response=analysis.suggested_response,
        suggested_follow_up_date=follow_up_date,
    )


# --- Settings ---
@router.get("/api/settings/weights", tags=["Settings"])
def get_scoring_weights(db: Session = Depends(get_db), _: UserAccount = Depends(get_current_user)):
    setting = db.query(UserSetting).filter(UserSetting.key == "scoring_weights").first()
    return setting.value if setting else {
        "skill_match": 0.30,
        "eligibility_match": 0.25,
        "role_relevance": 0.20,
        "location_preference": 0.10,
        "referral_freshness": 0.15,
        "high_match_threshold": 75,
    }


@router.put("/api/settings/weights", tags=["Settings"])
def update_scoring_weights(
    payload: ScoringWeightsUpdate,
    db: Session = Depends(get_db),
    _: UserAccount = Depends(get_current_user),
):
    setting = db.query(UserSetting).filter(UserSetting.key == "scoring_weights").first()
    if not setting:
        setting = UserSetting(key="scoring_weights", value=payload.model_dump())
        db.add(setting)
    else:
        setting.value = payload.model_dump()
    db.commit()
    return setting.value


# --- Telegram Webhook ---
@router.post("/api/telegram/webhook", tags=["Telegram"])
async def telegram_webhook(
    update: dict,
    x_telegram_bot_api_secret_token: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Telegram webhook secret.")
    return await telegram_service.handle_webhook_update(db, update)

