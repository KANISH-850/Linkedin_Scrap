# ReferralPilot AI — Security Architecture

## 1. Authentication & Session Management
- **Password Storage**: Uses `bcrypt` with automatic salting.
- **API Security**: Stateless JSON Web Tokens (JWT) using `HS256` with configurable expiry (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Endpoint Protection**: All sensitive APIs (`/api/profile`, `/api/opportunities`, `/api/discovery/run`) require valid `Bearer <token>` headers.
- **Initial Setup Lockdown**: `/api/auth/setup` only allows creating the initial admin account once. If any account exists, it returns HTTP 403 Forbidden.

## 2. Rate Limiting
- **In-Memory Sliding Window**: Protects sensitive endpoints against brute force and abuse:
  - `/api/auth/login`: Limited to 10 requests per 60 seconds per IP.
  - `/api/discovery/run`: Limited to 5 requests per 300 seconds per IP.

## 3. LinkedIn Terms of Service Compliance Guard
- **Strict Prohibition**: The system never logs into LinkedIn, never automates browser sessions against LinkedIn, and never scrapes authenticated pages.
- **Adapter Guard**: All discovery adapters reject URLs with `linkedin.com` or `lnkd.in` hostnames (`ValueError`).
- **User-Assisted Workflow**: For LinkedIn opportunities, the candidate voluntarily pastes the post text, and outreach is conducted manually by the candidate.

## 4. Telegram Security
- **Strict Authorization**: Commands and digests only process requests matching `TELEGRAM_AUTHORIZED_USER_ID`. Unknown users receive an unauthorized denial and their interactions are logged in `telegram_update_logs`.
- **Webhook Verification**: Webhook payloads are verified against `X-Telegram-Bot-Api-Secret-Token`.
- **Idempotency**: All Telegram `update_id`s are logged and verified to prevent duplicate execution.

## 5. Secret Hygiene
- `.env` and local database files are ignored by `.gitignore`.
- Exception traces in production do not reveal database credentials or secret keys.

