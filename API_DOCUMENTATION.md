# ReferralPilot AI — API Reference

## Authentication

### `POST /api/auth/login`
- **Body**: `{"email": "string", "password": "string"}`
- **Response**: `{"access_token": "string", "token_type": "bearer", "user_email": "string", "full_name": "string"}`

### `GET /api/auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `UserAccountOut`

---

## Candidate Profile

### `GET /api/profile`
- Returns candidate profile, technical skills, projects, and career targets.

### `PUT /api/profile`
- Updates candidate fields, skills, and projects.

---

## Opportunities

### `GET /api/opportunities`
- **Query Params**:
  - `category`: `referrals | internships | fresher_jobs | hackathons | scholarships | courses | research`
  - `min_score`: float (0 - 100)
  - `tracking_status`: `NEW | INTERESTED | APPLIED | ...`
  - `search`: text query
  - `page`: integer
  - `page_size`: integer
- **Response**: `PaginatedOpportunities`

### `GET /api/opportunities/{id}`
- Returns full opportunity record with extracted criteria, score breakdown, evidence, and drafts.

### `PATCH /api/opportunities/{id}/status`
- Updates tracking status and records an audit timestamp in `opportunity_status_history`.

### `POST /api/opportunities/{id}/draft-message`
- **Body**: `{"draft_type": "connection_request | referral_request | recruiter_outreach | follow_up", "contact_name": "string"}`
- Generates tailored outreach message.

---

## Follow-ups & Applications

### `GET /api/follow-ups` & `POST /api/opportunities/{id}/follow-up`
- Create and review scheduled outreach follow-ups.

### `GET /api/applications` & `POST /api/applications`
- Track officially submitted applications with resume versions.

---

## Discovery & Sources

### `GET /api/sources` & `PATCH /api/sources/{id}`
- Manage and toggle individual discovery adapters.

### `POST /api/discovery/run`
- Triggers an immediate discovery run across all enabled sources.

### `POST /api/discovery/submit`
- Submit a public URL and/or announcement text for instant AI analysis.
