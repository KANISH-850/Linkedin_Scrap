# ReferralPilot AI — System Architecture

## 1. Architectural Overview

ReferralPilot AI is designed as an autonomous, persistent career and opportunity intelligence assistant. It decouples long-running daily scheduled discovery from the user's local workstation, running entirely in the cloud on **Render** (FastAPI Web Service + Render Cron Job) backed by **Supabase PostgreSQL** and alerting via the **Telegram Bot API**.

```
                   +----------------------------------+
                   |       Vercel / Cloud CDN         |
                   |  React + TS Dashboard (Vite)     |
                   +-----------------+----------------+
                                     | REST (JWT)
                                     v
                   +----------------------------------+
                   |       Render Web Service         |
                   |     FastAPI Backend (Py 3.13)    |
                   +--------+----------------+--------+
                            |                |
             Cron Trigger   |                | Webhook / Alerts
    +-----------------------+                +---------------------+
    |                                                              |
    v                                                              v
+------------------------+                             +------------------------+
|    Render Cron Job     |                             |   Telegram Bot API     |
| (Daily 9:00 AM IST)    |                             | (Alerts & Reply Intel) |
+-----------+------------+                             +------------------------+
            |
            | Reads / Writes
            v
+-----------------------------------------------------+
|              Supabase PostgreSQL                    |
| (Opportunities, Profile, Tracking, Scores, Drafts)   |
+-----------------------------------------------------+
```

## 2. Component Breakdown

### A. Modular Discovery Framework (`app/discovery/`)
- **Adapters**: Pluggable adapters (`Remotive`, `Arbeitnow`, `RemoteOK`, `arXiv`, `HuggingFace`, `GenericRSS`, `ManualSubmission`).
- **URL Normalization**: Canonicalizes URLs by stripping tracking tokens (`utm_*`, `fbclid`, `gclid`, etc.).
- **Deduplication Hash**: `SHA256(category + organization + title)` ensures unique roles at the same company are never merged while avoiding duplicate records.
- **LinkedIn Compliance Guard**: Automated scraping or login to LinkedIn is strictly forbidden. The system allows processing user-supplied public links and text voluntarily provided by the candidate, redirecting the user to execute outreach actions manually.

### B. Provider-Independent AI Intelligence (`app/ai/`)
- Configurable via `LLM_PROVIDER`: supports OpenAI-compatible endpoints (`openai`), Google Gemini, and local Ollama.
- **Deterministic Heuristic Fallback**: If LLM API keys are absent or rate-limited, the system falls back to a deterministic, offline rule-based scoring and classification engine with zero downtime and no hallucinated data.
- **Eligibility Assessment**: Enforces mandatory graduation year (2028), experience requirements, and skill matching.

### C. Opportunity Lifecycle & Tracking (`app/models/`)
Tracks full progression through distinct statuses:
`NEW` -> `REVIEWED` -> `INTERESTED` -> `CONNECTION_PENDING` -> `CONNECTED` -> `REPLY_RECEIVED` -> `REFERRAL_RECEIVED` -> `APPLICATION_READY` -> `APPLIED` -> `INTERVIEW` -> `REJECTED` -> `CLOSED` -> `EXPIRED` -> `DISMISSED`.

### D. Hosted Scheduler (`app/scheduler/`)
- Executes at **09:00 AM IST (Asia/Kolkata)**.
- In production, configured on Render as a daily cron at `30 3 * * *` (03:30 UTC = 09:00 AM IST).
- Local fallback uses APScheduler for development only.

