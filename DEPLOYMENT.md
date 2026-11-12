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

Render uses `render.yaml` in this repository for single-click Blueprint deployment.

1. Push this repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com), click **New** -> **Blueprint**.
3. Connect your repository. Render will automatically detect the two services in `render.yaml`:
   - `referralpilot-ai-backend` (Web Service)
   - `referralpilot-ai-daily-discovery` (Cron Job scheduled at `30 3 * * *` UTC = 09:00 AM IST)
4. Fill in the environment variables:
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
2. Select your repository.
3. Set **Root Directory** to `frontend`.
4. Framework Preset: **Vite**.
5. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://<your-render-backend-url>`
6. Click **Deploy**.
