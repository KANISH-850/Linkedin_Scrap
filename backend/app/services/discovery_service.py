"""Discovery orchestrator: coordinates sources, deduplication, AI processing, DB persistence, and alerts."""

import asyncio
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session

from app.ai.service import ai_service
from app.core.config import get_settings
from app.core.logging import get_logger
from app.discovery.adapters import ADAPTER_REGISTRY, RawOpportunity
from app.discovery.base import (
    canonicalize_url,
    compute_dedup_hash,
    verify_url_reachable,
)
from app.models.models import (
    DiscoveryRun,
    DiscoverySource,
    EligibilityAssessment,
    Opportunity,
    OpportunityEvidence,
    OpportunityScore,
    OpportunitySource as OppSourceLink,
    UserProfile,
    UserSetting,
)
from app.telegram.service import telegram_service

logger = get_logger(__name__)


class DiscoveryEngine:
    """Manages full discovery runs with concurrency locks and partial failure handling."""

    async def execute_run(self, db: Session, trigger_type: str = "manual") -> DiscoveryRun:
        lock_id = str(uuid.uuid4())
        run = DiscoveryRun(
            status="running",
            trigger_type=trigger_type,
            lock_key=lock_id,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        settings = get_settings()
        errors: list[dict] = []
        sources_checked = 0
        sources_failed = 0
        opps_discovered = 0
        new_opps = 0
        high_match_count = 0

        # Load profile and settings
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

        active_sources = db.query(DiscoverySource).filter(DiscoverySource.enabled.is_(True)).all()

        for source in active_sources:
            adapter = ADAPTER_REGISTRY.get(source.adapter_key)
            if not adapter:
                continue

            sources_checked += 1
            try:
                raw_items = await adapter.fetch_with_retries(
                    config=source.config_json or {},
                    timeout=settings.discovery_request_timeout_seconds,
                    max_items=settings.discovery_max_items_per_source,
                )
                source.last_run_at = datetime.now(timezone.utc)
                source.last_status = "success"
                source.last_error = None
                db.commit()

                for raw in raw_items:
                    opps_discovered += 1
                    is_new, opp = await self._persist_raw_opportunity(db, raw, source.id, profile_dict, weights)
                    if is_new and opp:
                        new_opps += 1
                        if opp.score and opp.score.overall_score >= settings.high_match_threshold:
                            high_match_count += 1
                            # Send Telegram alert for high match
                            try:
                                await telegram_service.send_opportunity_alert(db, opp)
                            except Exception as alert_exc:
                                logger.warning(f"Telegram alert error for opp {opp.id}: {alert_exc}")

            except Exception as exc:
                sources_failed += 1
                source.last_run_at = datetime.now(timezone.utc)
                source.last_status = "failed"
                source.last_error = str(exc)[:500]
                db.commit()
                logger.error(f"Discovery source {source.name} failed: {exc}")
                errors.append({"source": source.name, "error": str(exc)[:300]})

        run.finished_at = datetime.now(timezone.utc)
        run.status = "completed" if sources_failed < sources_checked else "failed"
        run.sources_checked = sources_checked
        run.sources_failed = sources_failed
        run.opportunities_discovered = opps_discovered
        run.new_opportunities = new_opps
        run.high_match_count = high_match_count
        run.errors_json = errors
        run.summary_text = (
            f"Processed {sources_checked} sources ({sources_failed} failed). "
            f"Found {opps_discovered} opportunities ({new_opps} new, {high_match_count} high match)."
        )
        db.commit()

        # Send Telegram daily digest (delivers even when 0 new opportunities)
        try:
            await telegram_service.send_daily_digest(db, run)
        except Exception as digest_exc:
            logger.warning(f"Failed to send Telegram digest: {digest_exc}")

        return run

    async def _persist_raw_opportunity(
        self,
        db: Session,
        raw: RawOpportunity,
        source_id: int | None,
        profile_dict: dict,
        weights: dict,
    ) -> tuple[bool, Opportunity | None]:
        canonical = canonicalize_url(raw.source_url)
        dedup = compute_dedup_hash(raw.organization, raw.title, raw.category_hint, canonical)

        existing = db.query(Opportunity).filter(Opportunity.dedup_hash == dedup).first()
        if existing:
            # Attach source link if not present
            if source_id:
                link_exists = (
                    db.query(OppSourceLink)
                    .filter(OppSourceLink.opportunity_id == existing.id, OppSourceLink.discovery_source_id == source_id)
                    .first()
                )
                if not link_exists:
                    db.add(
                        OppSourceLink(
                            opportunity_id=existing.id,
                            discovery_source_id=source_id,
                            raw_url=raw.source_url,
                            external_id=raw.external_id,
                            raw_payload=raw.raw_payload,
                        )
                    )
                    db.commit()
            return False, existing

        # AI Extraction & Classification
        context = {
            "category_hint": raw.category_hint,
            "organization": raw.organization,
        }
        extracted = await ai_service.extract_and_classify(raw.description, raw.title, context)

        # Verification check
        verif_status = "unverified"
        if raw.application_url or raw.source_url:
            verif_status = await verify_url_reachable(raw.application_url or raw.source_url)

        # Build Opportunity record
        opp = Opportunity(
            title=raw.title,
            organization=raw.organization,
            category=extracted.category or raw.category_hint,
            subcategory=extracted.subcategory,
            description=raw.description,
            location=raw.location if raw.location != "Not specified" else extracted.location,
            is_remote=raw.is_remote or extracted.is_remote,
            is_hybrid=raw.is_hybrid or extracted.is_hybrid,
            deadline=raw.deadline,
            posted_at=raw.posted_at,
            active_status="active",
            verification_status=verif_status,
            canonical_url=canonical,
            source_url=raw.source_url,
            application_url=raw.application_url,
            dedup_hash=dedup,
            referral_classification=extracted.referral_classification,
            referral_confidence=extracted.referral_confidence,
            referral_instructions=extracted.referral_instructions,
            required_skills=list(set(raw.required_skills + extracted.required_skills)),
            preferred_skills=extracted.preferred_skills,
            education_requirement=extracted.education_requirement,
            graduation_year_requirement=extracted.graduation_year_requirement,
            experience_requirement=extracted.experience_requirement,
            compensation_or_stipend=raw.compensation_or_stipend or extracted.compensation_or_stipend,
            duration=raw.duration or extracted.duration,
            extra_metadata=raw.extra_metadata,
            ai_status="completed",
            tracking_status="NEW",
        )
        db.add(opp)
        db.flush()

        # Opportunity Source link
        if source_id:
            db.add(
                OppSourceLink(
                    opportunity_id=opp.id,
                    discovery_source_id=source_id,
                    raw_url=raw.source_url,
                    external_id=raw.external_id,
                    raw_payload=raw.raw_payload,
                )
            )

        # Evidence
        if raw.evidence_excerpt or extracted.referral_evidence_excerpt:
            db.add(
                OpportunityEvidence(
                    opportunity_id=opp.id,
                    evidence_type="source_excerpt",
                    source_url=raw.source_url,
                    excerpt=(raw.evidence_excerpt or extracted.referral_evidence_excerpt or "")[:1500],
                    author_name=raw.author_name or extracted.recruiter_or_author_name,
                )
            )

        # AI Eligibility & Scoring
        opp_dict = {
            "title": opp.title,
            "organization": opp.organization,
            "category": opp.category,
            "description": opp.description,
            "location": opp.location,
            "is_remote": opp.is_remote,
            "required_skills": opp.required_skills,
            "graduation_year_requirement": opp.graduation_year_requirement,
            "experience_requirement": opp.experience_requirement,
            "referral_classification": opp.referral_classification,
        }
        elig_res, score_res = await ai_service.evaluate_eligibility_and_score(profile_dict, opp_dict, weights)

        db.add(
            EligibilityAssessment(
                opportunity_id=opp.id,
                status=elig_res.status,
                matched_requirements=elig_res.matched_requirements,
                missing_requirements=elig_res.missing_requirements,
                disqualifying_requirements=elig_res.disqualifying_requirements,
                verification_questions=elig_res.verification_questions,
                summary=elig_res.summary,
            )
        )
        db.add(
            OpportunityScore(
                opportunity_id=opp.id,
                overall_score=score_res.overall_score,
                skill_score=score_res.skill_score,
                eligibility_score=score_res.eligibility_score,
                relevance_score=score_res.relevance_score,
                location_score=score_res.location_score,
                referral_freshness_score=score_res.referral_freshness_score,
                explanation=score_res.explanation,
                recommended_action=score_res.recommended_action,
                scoring_model="job_internship",
            )
        )

        db.commit()
        db.refresh(opp)
        return True, opp


discovery_engine = DiscoveryEngine()

