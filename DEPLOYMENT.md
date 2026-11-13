# ReferralPilot AI — Deployment Guide

## Production Topology

1. **Database**: Supabase PostgreSQL (Managed, SSL required)
2. **Backend**: Render Web Service (FastAPI, Python 3.12+)
3. **Daily Scheduler**: Render Cron Job (`30 3 * * *` UTC = 9:00 AM IST)
4. **Frontend**: Vercel (React + Vite)
5. **Notifications**: Telegram Bot API

---

## 1. Database Setup (Supabase PostgreSQL)

1. Create a project on [Supabase](https://supabase.com).
2. Go to **Project Settings** -> **Database** -> **Connection string** -> Select **URI** (or Transaction Pooler on port 6543).
3. Copy the URI. It will look like:
   ```
   postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require
   ```
4. Update `DATABASE_URL` in your backend environment variables (FastAPI will automatically use psycopg v3).

---

## 2. Telegram Bot Setup (BotFather)

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`, name your bot (e.g. `ReferralPilotBot`), and choose a username ending in `bot`.
3. Copy the **HTTP API Bot Token** -> this is your `TELEGRAM_BOT_TOKEN`.
4. Message `@userinfobot` on Telegram to get your numeric Telegram User ID. Copy this value -> this is your `TELEGRAM_AUTHORIZED_USER_ID`.
5. Optional Webhook: After deploying your backend to Render:
   ```bash
   curl -F "url=https://<your-render-backend-url>/api/telegram/webhook" \
        -F "secret_token=<YOUR_TELEGRAM_WEBHOOK_SECRET>" \
        https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook
   ```

---

## 3. Backend & Cron Deployment (Render)

### Option A: Using Blueprint (Recommended)
Render uses `render.yaml` in this repository for automatic multi-service deployment.
1. Push this repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com), click **New** -> **Blueprint**.
3. Connect your repository. Render will automatically configure both services:
   - `referralpilot-ai-backend` (Web Service, rootDir: `backend`)
   - `referralpilot-ai-daily-discovery` (Cron Job, rootDir: `backend`, schedule: `30 3 * * *` UTC = 9:00 AM IST)

### Option B: Manual Web Service Setup
If configuring the service manually in the Render dashboard:
1. Click **New** -> **Web Service** -> Connect repository.
2. Configure settings:
   - **Root Directory**: `backend` *(CRITICAL: must be set to `backend`)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variable**: `PYTHON_VERSION` = `3.11.9`
3. Fill in the environment variables:
   - `DATABASE_URL`: Your Supabase connection string.
   - `SECRET_KEY`: A 64-character random string.
   - `ADMIN_EMAIL`: Your initial login email (e.g. `admin@referralpilot.app`).
   - `ADMIN_PASSWORD`: Strong password.
   - `FRONTEND_URL`: URL of your deployed frontend on Vercel.
   - `TELEGRAM_BOT_TOKEN`: Token from BotFather.
   - `TELEGRAM_AUTHORIZED_USER_ID`: Your numeric Telegram ID.
   - `LLM_PROVIDER`: `heuristic` (free/offline) or `openai` (if you supply `LLM_API_KEY`).

---

## 4. Frontend Deployment (Vercel)

1. In [Vercel](https://vercel.com), click **Add New** -> **Project**.
2. Select your repository `Linkedin_Scrap`.
3. Set **Root Directory** to `frontend`.
4. Framework Preset: **Vite**.
5. Add Environment Variable:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://<your-render-backend-url>` (e.g. `https://linkedin-scrap-q1zb.onrender.com`)
   - **Type**: Select **Config** (not Secret, as Vite framework prefixes expose values to the client bundle).
6. Click **Deploy**.

### Vercel Reverse Proxy Architecture
The repository includes `frontend/vercel.json` and root `vercel.json` with reverse-proxy rewrites:
```json
{
  "rewrites": [
    { "source": "/api/:match*", "destination": "https://<your-render-backend-url>/api/:match*" },
    { "source": "/health", "destination": "https://<your-render-backend-url>/health" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```
This architecture prevents `405 Method Not Allowed` errors by proxying all `/api/*` POST/PUT/DELETE requests directly to the FastAPI backend, while preserving client-side SPA routing for all dashboard views.

---

## 5. Operations & Verification Checklist

### System Health Diagnostic
Verify your live backend health:
```bash
curl -s https://<your-render-backend-url>/health | jq
```
Expected production response:
```json
{
  "status": "healthy",
  "app": "ReferralPilot AI",
  "version": "1.0.0",
  "environment": "production",
  "database": {
    "status": "connected",
    "latency_ms": 15.4
  },
  "stats": {
    "persisted_opportunities": 0
  }
}
```

### Initial Opportunity Discovery
Once deployed against a fresh database, initial metrics will display `0` until discovery is executed.
Trigger live multi-source discovery using:
1. **Frontend UI**: Click the green **"Run Discovery Now"** button in the dashboard sidebar.
2. **API Endpoint**:
   ```bash
   curl -X POST https://<your-render-backend-url>/api/discovery/run \
        -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
   ```
3. **Automated Cron**: The Render Cron Job will run automatically every day at 09:00 AM IST (`30 3 * * *` UTC).

---

## 6. Production Troubleshooting Matrix

| Symptom | Probable Cause | Remediation |
| :--- | :--- | :--- |
| `HTTP 405 Method Not Allowed` | Frontend POST routed to static `/index.html` | Ensure `vercel.json` proxy rewrites are present and redeploy Vercel. |
| `No config file 'alembic.ini' found` | Render build executed from repo root | Ensure root `alembic.ini` is present or set Render **Root Directory** to `backend`. |
| `psycopg.OperationalError: connection failed` | Supabase IPv6 direct host blocked on Render IPv4 | Switch connection string to Supabase Pooler (`pooler.supabase.com:5432`) with `?sslmode=require`. |
| `401 Authentication required` | Calling protected endpoints without JWT | Log in through `/api/auth/login` to obtain an access token. |
| `CORS Error in Browser Console` | Vercel domain not listed in backend `CORS_ORIGINS` | Add `https://<your-vercel-domain>.vercel.app` to `FRONTEND_URL` and `CORS_ORIGINS` in Render settings. |


