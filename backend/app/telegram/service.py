"""Telegram Bot integration with strict authorization, idempotency, and rich digests."""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.ai.service import ai_service
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.models import (
    DiscoveryRun,
    FollowUp,
    Notification,
    Opportunity,
    OpportunityScore,
    TelegramUpdateLog,
    UserProfile,
)

logger = get_logger(__name__)


class TelegramService:
    """Handles outbound alerts/digests and inbound webhook commands."""

    def _bot_api_url(self, method: str) -> str:
        token = get_settings().telegram_bot_token
        return f"https://api.telegram.org/bot{token}/{method}"

    async def send_message(
        self,
        chat_id: str,
        text: str,
        reply_markup: Optional[dict[str, Any]] = None,
    ) -> tuple[bool, Optional[str]]:
        settings = get_settings()
        if not settings.telegram_bot_token:
            logger.info("TELEGRAM_BOT_TOKEN not configured; skipping Telegram send.")
            return False, "TELEGRAM_BOT_TOKEN not configured"

        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text[:4096],
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self._bot_api_url("sendMessage"), json=payload)
                if resp.status_code == 200 and resp.json().get("ok"):
                    return True, None
                err = resp.text[:300]
                logger.warning(f"Telegram sendMessage failed: {err}")
                return False, err
        except Exception as exc:
            logger.error(f"Telegram sendMessage exception: {exc}")
            return False, str(exc)

    async def send_opportunity_alert(self, db: Session, opp: Opportunity) -> bool:
        settings = get_settings()
        chat_id = settings.telegram_authorized_user_id
        if not chat_id:
            return False

        dedup_key = f"high_match_opp:{opp.id}"
        if db.query(Notification).filter(Notification.dedup_key == dedup_key).first():
            return False

        score_val = opp.score.overall_score if opp.score else 0.0
        elig_status = opp.eligibility.status if opp.eligibility else "Unverified"
        deadline_str = opp.deadline.isoformat() if opp.deadline else "Not specified"
        explanation = opp.score.explanation if opp.score else "Matched your profile."
        next_action = opp.score.recommended_action if opp.score else "Review details"
        dashboard_link = f"{settings.frontend_url.rstrip('/')}/opportunities/{opp.id}"
        apply_link = opp.application_url or opp.source_url

        text = (
            f"🎯 <b>High-Match Opportunity ({score_val:.0f}/100)</b>\n"
            f"<b>{opp.title}</b>\n"
            f"🏢 {opp.organization} | 📂 {opp.category}\n"
            f"📍 {opp.location}\n"
            f"✅ Eligibility: {elig_status}\n"
            f"⏰ Deadline: {deadline_str}\n"
            f"💡 Why it matches: {explanation}\n"
            f"👉 Next action: {next_action}"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "📊 Open Dashboard", "url": dashboard_link},
                    {"text": "🔗 Source / Apply", "url": apply_link},
                ]
            ]
        }

        ok, err = await self.send_message(chat_id, text, reply_markup=reply_markup)
        notif = Notification(
            opportunity_id=opp.id,
            channel="telegram",
            notification_type="high_match_alert",
            dedup_key=dedup_key,
            payload={"title": opp.title, "score": score_val},
            status="sent" if ok else "failed",
            error_message=err,
            sent_at=datetime.now(timezone.utc) if ok else None,
        )
        db.add(notif)
        db.commit()
        return ok

    async def send_daily_digest(self, db: Session, run: DiscoveryRun) -> bool:
        settings = get_settings()
        chat_id = settings.telegram_authorized_user_id
        today_str = date.today().isoformat()
        dedup_key = f"daily_digest:{today_str}:{run.id}"

        if db.query(Notification).filter(Notification.dedup_key == dedup_key).first():
            return False

        needs_verif = (
            db.query(Opportunity)
            .filter(Opportunity.verification_status != "verified", Opportunity.active_status == "active")
            .count()
        )
        soon = date.today() + timedelta(days=7)
        deadlines_soon = (
            db.query(Opportunity)
            .filter(Opportunity.deadline.isnot(None), Opportunity.deadline <= soon, Opportunity.deadline >= date.today())
            .count()
        )
        followups_due = (
            db.query(FollowUp)
            .filter(FollowUp.status == "pending", FollowUp.due_date <= date.today())
            .count()
        )

        failed_sources = [e.get("source", "unknown") for e in (run.errors_json or [])]
        failed_line = ", ".join(failed_sources) if failed_sources else "None"

        text = (
            f"☀️ <b>ReferralPilot AI — Daily Digest ({today_str})</b>\n\n"
            f"🔎 Sources checked: <b>{run.sources_checked}</b>\n"
            f"📥 Opportunities discovered: <b>{run.opportunities_discovered}</b>\n"
            f"✨ New opportunities: <b>{run.new_opportunities}</b>\n"
            f"🎯 High-match opportunities: <b>{run.high_match_count}</b>\n"
            f"🧐 Needing manual verification: <b>{needs_verif}</b>\n"
            f"⏰ Deadlines approaching (7d): <b>{deadlines_soon}</b>\n"
            f"📌 Follow-ups due: <b>{followups_due}</b>\n"
            f"⚠️ Sources failed: {failed_line}\n\n"
            f"🔗 <a href=\"{settings.frontend_url}\">Open ReferralPilot Dashboard</a>"
        )

        ok = False
        err: Optional[str] = "TELEGRAM_AUTHORIZED_USER_ID not configured"
        if chat_id:
            ok, err = await self.send_message(chat_id, text)

        db.add(
            Notification(
                discovery_run_id=run.id,
                channel="telegram",
                notification_type="daily_digest",
                dedup_key=dedup_key,
                payload={"run_id": run.id, "new": run.new_opportunities},
                status="sent" if ok else "failed",
                error_message=err,
                sent_at=datetime.now(timezone.utc) if ok else None,
            )
        )
        db.commit()
        return ok

    async def handle_webhook_update(self, db: Session, update: dict[str, Any]) -> dict[str, Any]:
        settings = get_settings()
        update_id = update.get("update_id")
        message = update.get("message") or update.get("edited_message")
        if not message or update_id is None:
            return {"ok": True, "ignored": "no_message"}

        chat_id = str(message.get("chat", {}).get("id", ""))
        from_user_id = str(message.get("from", {}).get("id", ""))
        text = (message.get("text") or "").strip()

        # Idempotency check
        if db.query(TelegramUpdateLog).filter(TelegramUpdateLog.update_id == update_id).first():
            return {"ok": True, "duplicate": True}

        # Authorization check
        authorized_id = str(settings.telegram_authorized_user_id or "").strip()
        if not authorized_id or (from_user_id != authorized_id and chat_id != authorized_id):
            db.add(
                TelegramUpdateLog(
                    update_id=update_id,
                    chat_id=chat_id,
                    command=text[:50],
                    status="unauthorized",
                )
            )
            db.commit()
            await self.send_message(chat_id, "⛔ Unauthorized. This bot is restricted to its registered owner.")
            return {"ok": False, "reason": "unauthorized"}

        cmd = text.split()[0].lower() if text.startswith("/") else "reply_text"
        db.add(TelegramUpdateLog(update_id=update_id, chat_id=chat_id, command=cmd[:100], status="processed"))
        db.commit()

        reply_text = await self._dispatch_command(db, text)
        await self.send_message(chat_id, reply_text)
        return {"ok": True, "command": cmd}

    async def _dispatch_command(self, db: Session, text: str) -> str:
        settings = get_settings()
        cmd = text.split()[0].lower().split("@")[0] if text.startswith("/") else ""

        if cmd in ("/start", "/help"):
            return (
                "🤖 <b>ReferralPilot AI Assistant</b>\n\n"
                "Commands:\n"
                "/today — Today's summary\n"
                "/new — Latest discovered opportunities\n"
                "/referrals — Top referral opportunities\n"
                "/internships — Top internships\n"
                "/jobs — Fresher jobs\n"
                "/hackathons — Hackathons\n"
                "/scholarships — Scholarships\n"
                "/courses — Courses & certifications\n"
                "/research — Research opportunities\n"
                "/followups — Due follow-ups\n"
                "/status — Latest discovery run status\n"
                "/settings — Profile & scoring summary\n\n"
                "💡 <i>Tip: Paste any recruiter/employee reply here to get an instant AI classification and suggested response!</i>"
            )

        category_map = {
            "/referrals": "referrals",
            "/internships": "internships",
            "/jobs": "fresher_jobs",
            "/hackathons": "hackathons",
            "/scholarships": "scholarships",
            "/courses": "courses",
            "/research": "research",
        }

        if cmd in category_map:
            cat = category_map[cmd]
            opps = (
                db.query(Opportunity)
                .outerjoin(OpportunityScore)
                .filter(Opportunity.category == cat, Opportunity.active_status == "active")
                .order_by(OpportunityScore.overall_score.desc().nullslast(), Opportunity.discovered_at.desc())
                .limit(5)
                .all()
            )
            if not opps:
                return f"No active opportunities found in <b>{cat}</b> yet."
            lines = [f"📂 <b>Top {cat.replace('_', ' ').title()}</b>\n"]
            for o in opps:
                sc = f"{o.score.overall_score:.0f}/100" if o.score else "Unscored"
                lines.append(f"• <b>{o.title}</b> ({o.organization}) — {sc}\n  {settings.frontend_url}/opportunities/{o.id}")
            return "\n".join(lines)

        if cmd == "/new":
            opps = (
                db.query(Opportunity)
                .order_by(Opportunity.discovered_at.desc())
                .limit(5)
                .all()
            )
            if not opps:
                return "No opportunities discovered yet."
            lines = ["✨ <b>Latest Opportunities</b>\n"]
            for o in opps:
                lines.append(f"• [{o.category}] <b>{o.title}</b> at {o.organization}")
            return "\n".join(lines)

        if cmd == "/today":
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            new_today = db.query(Opportunity).filter(Opportunity.discovered_at >= today_start).count()
            total_active = db.query(Opportunity).filter(Opportunity.active_status == "active").count()
            due = db.query(FollowUp).filter(FollowUp.status == "pending", FollowUp.due_date <= date.today()).count()
            return (
                f"📊 <b>Today's Snapshot</b>\n"
                f"• New today: <b>{new_today}</b>\n"
                f"• Total active: <b>{total_active}</b>\n"
                f"• Follow-ups due: <b>{due}</b>"
            )

        if cmd == "/followups":
            fups = (
                db.query(FollowUp)
                .filter(FollowUp.status == "pending")
                .order_by(FollowUp.due_date.asc())
                .limit(5)
                .all()
            )
            if not fups:
                return "✅ No pending follow-ups!"
            lines = ["📌 <b>Pending Follow-ups</b>\n"]
            for f in fups:
                opp = db.query(Opportunity).filter(Opportunity.id == f.opportunity_id).first()
                title = opp.title if opp else f"Opportunity #{f.opportunity_id}"
                lines.append(f"• {f.due_date.isoformat()}: <b>{title}</b> ({f.notes or 'No notes'})")
            return "\n".join(lines)

        if cmd == "/status":
            run = db.query(DiscoveryRun).order_by(DiscoveryRun.started_at.desc()).first()
            if not run:
                return "No discovery runs recorded yet."
            return (
                f"⚙️ <b>Latest Discovery Run (#{run.id})</b>\n"
                f"• Status: <b>{run.status}</b> ({run.trigger_type})\n"
                f"• Sources checked: {run.sources_checked} (Failed: {run.sources_failed})\n"
                f"• Discovered: {run.opportunities_discovered} | New: {run.new_opportunities}\n"
                f"• High match: {run.high_match_count}"
            )

        if cmd == "/settings":
            profile = db.query(UserProfile).first()
            if not profile:
                return "Candidate profile not configured."
            return (
                f"👤 <b>Profile Summary</b>\n"
                f"• Target: {profile.target_career_positioning}\n"
                f"• Institution: {profile.institution} ({profile.graduation_year})\n"
                f"• Goal: {profile.career_goal}\n"
                f"• Preferred Locations: {', '.join(profile.preferred_locations)}"
            )

        # Otherwise treat as pasted reply text for AI Reply Intelligence
        profile = db.query(UserProfile).first()
        profile_dict = {
            "full_name": profile.full_name if profile else "Kanish K",
            "target_career_positioning": profile.target_career_positioning if profile else "AI Engineer",
        }
        analysis = await ai_service.analyze_reply(text, None, profile_dict)
        return (
            f"🧠 <b>Reply Intelligence</b>\n"
            f"• Classification: <b>{analysis.classification}</b>\n"
            f"• Explanation: {analysis.explanation}\n"
            f"• Next step: {analysis.recommended_next_step}\n\n"
            f"📝 <b>Suggested Response (review before sending):</b>\n<i>{analysis.suggested_response}</i>"
        )


telegram_service = TelegramService()

