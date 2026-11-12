# ReferralPilot AI

> **Personal AI-Powered Career Opportunity Intelligence & Referral Management Assistant**

ReferralPilot AI is an autonomous, production-ready platform designed for **Kanish K** (3rd-year B.E. Computer Science student at Bannari Amman Institute of Technology, graduating in 2028, targeting AI Engineer roles).

It operates completely independently of your local workstation, discovering relevant opportunities every day, analyzing them against your candidate profile, identifying referral possibilities, drafting personalized messages, tracking outreach, and sending a daily Telegram digest.

---

## Key Highlights

- **Zero Workstation Dependency**: Runs on **Render Web Service** + **Render Cron Job** (09:00 AM IST daily) with **Supabase PostgreSQL**. Antigravity and your laptop do NOT need to remain open.
- **7 Opportunity Verticals**:
  1. Referrals (Confirmed employee offers, referral requests, hiring posts)
  2. Internships (AI/ML, Python, Software Engineering)
  3. Fresher Jobs (Graduate Trainee, Associate Software Engineer)
  4. Hackathons (Smart India, AI Innovation Challenges)
  5. Scholarships (Merit-based, technical grants)
  6. Courses & Certifications (Industry-recognized pathways)
  7. Research (arXiv AI/ML/NLP preprints, faculty research)
- **LinkedIn Terms of Service Compliant**: Never scrapes LinkedIn or automates LinkedIn accounts. Safely analyzes voluntarily submitted post text and redirects the candidate to perform outreach manually.
- **Provider-Independent AI**: Configurable for OpenAI, Gemini, or local models, with a built-in deterministic heuristic fallback for 100% offline reliability without hallucinating eligibility or salaries.
- **Telegram Bot Assistant**: Daily 9 AM IST digest, high-match alerts, deadline reminders, and instant reply intelligence.

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- Node.js 18+

### 2. Backend Setup
```bash
# Set up venv and install dependencies
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# Run migrations and seed default candidate profile & sources
.venv\Scripts\alembic upgrade head
.venv\Scripts\python -c "from app.database.session import SessionLocal; from app.database.seed import seed_database; db = SessionLocal(); seed_database(db); db.close()"

# Start backend server
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to access the dashboard.
- Default Admin: `admin@referralpilot.app`
- Default Password: `ChangeMeStrongPassword123!`

---

## Testing

```bash
# Run backend pytest suite (10 tests)
cd backend
.venv\Scripts\pytest -v

# Run frontend Vitest suite
cd frontend
npm run test
```

---

## Documentation
- [Architecture Details](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Security Architecture](SECURITY.md)
- [Testing Report](TESTING.md)
- [Operational Runbook](OPERATIONS.md)
- [API Documentation](API_DOCUMENTATION.md)
