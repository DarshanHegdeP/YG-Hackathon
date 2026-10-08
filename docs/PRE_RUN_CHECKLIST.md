# Pre-Run Checklist & Operator Setup Guide

This checklist is for anyone cloning the **AI-Powered Evidence Collection Bot** repository who wants to set up and run the system locally, run automated tests, and prepare for production deployment.

---

## A. Software Prerequisites

Verify the following software tools are installed on your machine:

| Requirement | Minimum Version | Recommended Version | Verification Command |
|---|---|---|---|
| **Python** | 3.10+ | 3.11 – 3.13 | `python --version` |
| **Node.js** | 18.0+ | 20.x LTS | `node --version` |
| **npm** | 9.0+ | 10.x | `npm --version` |
| **Git** | 2.30+ | Latest | `git --version` |

---

## B. Cloud Services & API Accounts Required

To enable all cloud features in production, you will need:

1. **Supabase** ([https://supabase.com](https://supabase.com))
   - Free-tier PostgreSQL database
   - Free-tier S3-compatible File Storage bucket (`evidence-files`)
2. **Google AI Studio (Gemini)** ([https://aistudio.google.com](https://aistudio.google.com))
   - Gemini API key for structured document audit interpretation (`gemini-1.5-flash`)
3. **Resend** ([https://resend.com](https://resend.com))
   - Free-tier transactional email delivery API
4. **Render** ([https://render.com](https://render.com)) *(For backend deployment)*
5. **Vercel** ([https://vercel.com](https://vercel.com)) *(For frontend deployment)*

> **Note for Local Testing / Offline Demos:**
> The application includes smart fallbacks for all external services!
> - If `DATABASE_URL` is set to SQLite (`sqlite:///./evidence_bot.db`), it runs with zero database setup.
> - If `SUPABASE_URL` is omitted, uploaded files are stored locally in `./storage_uploads`.
> - If `GEMINI_API_KEY` is omitted, the built-in deterministic auditor validates requirements.
> - If `RESEND_API_KEY` is omitted, emails are logged to the terminal console and recorded in the database audit log.

---

## C. Supabase Setup Instructions

1. **Create Project**:
   - Go to [Supabase Dashboard](https://app.supabase.com) and click **New project**.
   - Note your database password.
2. **Retrieve PostgreSQL Connection String**:
   - Go to **Project Settings** → **Database** → **Connection string** (URI).
   - Format: `postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:65432/postgres`
   - Paste this into `DATABASE_URL` in `backend/.env`.
3. **Create Storage Bucket**:
   - In Supabase sidebar, select **Storage**.
   - Click **New Bucket**.
   - Name: `evidence-files`.
   - Set to **Public** or configure bucket policy to allow upload/download with service role key.
4. **Retrieve API Keys**:
   - Go to **Project Settings** → **API**.
   - Copy **Project URL** (`SUPABASE_URL`).
   - Copy **service_role secret key** (`SUPABASE_SERVICE_ROLE_KEY`).

---

## D. Google Gemini Setup Instructions

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Click **Create API Key**.
3. Copy the key and set `GEMINI_API_KEY` in `backend/.env`.
4. The default model is `gemini-1.5-flash`. You can configure this with `GEMINI_MODEL`.

---

## E. Resend Email Setup Instructions

1. Go to [Resend](https://resend.com).
2. Create an API Key in the **API Keys** tab.
3. If using the default sandbox sender, set `EMAIL_FROM=onboarding@resend.dev`.
   - *Limitation*: In Resend's free test tier, `onboarding@resend.dev` can only deliver emails to the email address registered with your Resend account.
   - For unrestricted sending, add and verify your custom domain in Resend.

---

## F. Environment Files Configuration

### 1. `backend/.env`
```env
# Database (PostgreSQL or local SQLite)
DATABASE_URL=sqlite:///./evidence_bot.db
# Or PostgreSQL:
# DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/[DBNAME]

# JWT Security
JWT_SECRET=hackathon-dev-secret-key-32-character-min-key-12345
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Supabase Storage (Optional locally; required for cloud storage)
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=evidence-files
LOCAL_STORAGE_DIR=./storage_uploads

# Gemini AI (Optional locally; uses deterministic fallback if blank)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash

# Email Service (Optional locally; logs to console if blank)
RESEND_API_KEY=
EMAIL_FROM=onboarding@resend.dev

# Frontend & CORS
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Scheduler
REMINDER_INTERVAL_MINUTES=60
REMINDER_1_DAYS_BEFORE=2
REMINDER_2_DAYS_BEFORE=1
ESCALATION_DAYS_AFTER=1
```

### 2. `frontend/.env`
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## G. Local Run Commands

### Backend:
```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Seed database with demo accounts, controls, scopes & historical requests
python seed.py

# 3. Run automated tests
pytest backend/tests/ -v

# 4. Start the FastAPI server (Runs on http://localhost:8000)
uvicorn app.main:app --reload --app-dir backend --port 8000
```

### Frontend:
```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server (Runs on http://localhost:5173)
npm run dev
```

---

## H. Verification Checklist

- [ ] `/health` returns `{"status": "ok"}` at `http://localhost:8000/health`.
- [ ] Login page displays at `http://localhost:5173/login`.
- [ ] 1-Click login as **Reviewer** (`reviewer@example.com` / `Password123!`) works.
- [ ] Dashboard displays 8 status metric cards, overdue alert banner, and recent request table.
- [ ] Controls tab lists `C001` (Periodic User Access Review) and `C002` (Production Change Management).
- [ ] Scopes tab displays all 4 scope targets (`IT Operations Team`, `Finance Team`, `John Smith`, `Payments Application`).
- [ ] Public Submission portal loads via `http://localhost:5173/submit/demo-token-itops-2026-0001`.
- [ ] Uploading `sample_evidence/Complete_Access_Review_Q3_2026.pdf` produces `COMPLETE` status and green audit findings.
- [ ] Uploading `sample_evidence/Incomplete_User_Roster.xlsx` produces `INCOMPLETE` status and lists missing requirements.
- [ ] APScheduler triggers reminders and logs communication events.
- [ ] Audit logs reflect all actions in `http://localhost:5173/audit-logs`.

---

## I. Common Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| **CORS Error in Browser** | Backend origins mismatch | Verify `CORS_ORIGINS` in `backend/.env` contains `http://localhost:5173`. |
| **`ImportError: email-validator`** | Missing pydantic email dependency | Run `pip install email-validator`. |
| **Bcrypt 72-byte ValueError** | Known passlib bug with bcrypt 4.1+ | Direct bcrypt utility in `app/utils/security.py` resolves this. |
| **Resend error 403 / unverified sender** | Free-tier sandbox limitation | Set recipient to your Resend account email or leave `RESEND_API_KEY` blank to use terminal mock mode. |
| **Port 8000 conflict** | Another process is using port 8000 | Run `uvicorn app.main:app --reload --app-dir backend --port 8001` and update `VITE_API_BASE_URL`. |
