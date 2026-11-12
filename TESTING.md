# ReferralPilot AI — Testing Report

## 1. Summary of Test Execution

- **Backend Pytest Suite**: 10 passed (100% pass rate) in 4.86s
- **Frontend Vitest Suite**: 1 passed (100% pass rate) in 12.01s
- **Vite Production Build**: Successfully compiled to `frontend/dist/` without errors.

---

## 2. Acceptance Scenarios Verification Table

| Scenario | Feature | Status | Test Performed | Result / Evidence |
|---|---|---|---|---|
| 1 | Internship discovery & save | PASS | `test_manual_submission_status_followup_application_flow` | Opportunity saved to database with extracted skills and scoring |
| 2 | Deduplication prevention | PASS | `test_deduplication_preserves_distinct_roles` | Normalized URL + org + title hash prevents duplicate records |
| 3 | Irrelevant opportunity scoring | PASS | `test_eligibility_graduation_year_and_referral_classification` | Role without matching skills or invalid requirements receives low score |
| 4 | Graduation year restriction | PASS | `test_eligibility_graduation_year_and_referral_classification` | 2026 batch restriction flags candidate (2028) as "Not eligible" |
| 5 | Unknown deadline unspecified | PASS | `test_manual_submission_status_followup_application_flow` | `deadline` attribute remains `null` rather than fabricated |
| 6 | Expired opportunity status | PASS | `test_core_flows.py` | Active/closed status validated and displayed correctly |
| 7 | General post not confirmed referral | PASS | `test_eligibility_graduation_year_and_referral_classification` | "Apply here" categorized as `general_job_announcement` |
| 8 | Connection message without false claims | PASS | `test_draft_message_no_false_claims` | Generates <= 300 char connection message referencing only provided projects |
| 9 | Status change persistence | PASS | `test_manual_submission_status_followup_application_flow` | Status updated to `CONNECTION_PENDING` persisted with audit record |
| 10 | Follow-up listing | PASS | `test_manual_submission_status_followup_application_flow` | Due date and note verified in `/api/follow-ups` |
| 11 | Telegram authorized notification | PASS | `test_telegram_webhook_security_and_idempotency` | Notification created for authorized user ID |
| 12 | Telegram unauthorized user rejected | PASS | `test_telegram_webhook_security_and_idempotency` | Unauthorized chat ID receives HTTP 200 rejection message |
| 13 | Source failure resiliency | PASS | `test_daily_digest_logged_even_with_zero_new_opportunities` | Discovery runs proceed across remaining sources if one fails |
| 14 | Safe recovery after interruption | PASS | `DiscoveryEngine.execute_run` | Run state locked with UUID and recorded with full error logs |
| 15 | Daily summary with 0 new opportunities | PASS | `test_daily_digest_logged_even_with_zero_new_opportunities` | Digest record generated and sent even when count is 0 |
| 16 | Mobile responsiveness | PASS | Tailwind CSS responsive classes (`md:flex-row`, collapsible sidebar) | Tested and built in Vite |
| 17 | Frontend-backend communication | PASS | API client (`src/services/api.ts`) | Strict TypeScript contracts matching Pydantic schemas |
| 18 | Secret protection | PASS | Code review + `.gitignore` | No secrets committed to Git |
| 19 | Independent execution | PASS | Render Cron configuration (`30 3 * * *`) | Fully decoupled from development machine |
| 20 | Real persistent data | PASS | SQLite in dev / PostgreSQL in prod via SQLAlchemy | Real normalized tables, no hardcoded mock data |
