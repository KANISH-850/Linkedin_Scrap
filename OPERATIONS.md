# ReferralPilot AI — Operational & Runbook Guide

## 1. Daily Discovery Schedule (Hosted on Render)
- **Schedule**: Daily at **09:00 AM IST (Asia/Kolkata)**.
- **Render Cron Definition**: `30 3 * * *` (03:30 UTC = 09:00 AM IST, UTC+5:30).
- **Command Executed**: `python -m app.scheduler.scheduler render_cron`
- **Execution Flow**:
  1. Loads candidate profile & enabled discovery sources.
  2. Executes adapters with exponential backoff (2 retries).
  3. Deduplicates items using canonicalized URLs and SHA256 hashes.
  4. Runs AI classification, eligibility check, and scoring.
  5. Dispatches high-match alerts and the daily Telegram digest.
  6. Records run summary in `discovery_runs`.

## 2. Manual Discovery Trigger
- **Via Dashboard**: Click **"Run Discovery Now"** in the sidebar.
- **Via CLI / Terminal**:
  ```bash
  cd backend
  .venv\Scripts\python.exe -m app.scheduler.scheduler manual_cli
  ```

## 3. Applying Database Migrations
```bash
cd backend
.venv\Scripts\alembic.exe upgrade head
```

## 4. Resetting Admin Account or Seeding Default Data
```bash
python scripts/setup_admin.py
```
