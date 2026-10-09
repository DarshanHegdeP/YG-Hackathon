# Pre-Run Checklist & Operator Setup Guide

This checklist is for anyone cloning the **AI-Powered Evidence Collection Bot (LOD2 Evidence Platform)** repository who wants to set up and run the system locally, run automated tests, and prepare for production deployment.

**Hosted URL**: [https://ygsupa.netlify.app/](https://ygsupa.netlify.app/)  
**Git Branch**: `feature/supa`

---

## A. Software Prerequisites

Verify the following software tools are installed on your machine:

| Requirement | Minimum Version | Recommended Version | Verification Command |
|---|---|---|---|
| **Python** | 3.10+ | 3.11 – 3.13 | `python --version` |
| **Node.js** | 18.0+ | 20.x LTS | `node --version` |
| **npm** | 9.0+ | 10.x | `npm --version` |
| **Docker** | 20.10+ | Latest | `docker --version` |
| **Git** | 2.30+ | Latest | `git --version` |

---

## B. Cloud Services & API Accounts Required

To enable all cloud features in production, you can configure:

1. **Supabase** ([https://supabase.com](https://supabase.com))
   - PostgreSQL database with connection pooling
   - S3-compatible Object Storage bucket (`evidence`) in region `ap-northeast-1`
2. **Google AI Studio (Gemini)** ([https://aistudio.google.com](https://aistudio.google.com))
   - Gemini API key for structured document audit interpretation (`gemini-1.5-flash` or `gemini-3.1-flash-lite`)
3. **Cloudflare Workers AI** ([https://developers.cloudflare.com/workers-ai/](https://developers.cloudflare.com/workers-ai/))
   - Account ID and API Token for CLEF model (`@cf/cloudflare/clef`) via Cloudflare AI Gateway
4. **Resend** ([https://resend.com](https://resend.com))
   - Transactional email delivery API
5. **Render** ([https://render.com](https://render.com)) *(For backend container deployment)*
6. **Netlify** ([https://netlify.com](https://netlify.com)) *(For frontend SPA deployment)*

> **Note for Local Testing / Offline Demos:**
> The application includes smart fallbacks for all external services!
> - If `DATABASE_URL` is set to SQLite (`sqlite:///./evidence_bot.db`), it runs with zero database setup.
> - If `SUPABASE_S3_ENDPOINT` is omitted, uploaded files are stored locally in `./storage_uploads`.
> - If `GEMINI_API_KEY` is omitted, the built-in deterministic auditor validates requirements.
> - If `RESEND_API_KEY` is omitted, emails are logged to the terminal console and recorded in the database audit log.

---

## C. Environment Files Configuration

### 1. `backend/.env`
```env
# Database (PostgreSQL or local SQLite)
DATABASE_URL=sqlite:///./evidence_bot.db

# JWT Security
JWT_SECRET=hackathon-dev-secret-key-32-character-min-key-12345
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Supabase S3-Compatible Storage
SUPABASE_URL=https://beerpsrntgbrcklhqesj.supabase.co
SUPABASE_STORAGE_BUCKET=evidence
SUPABASE_S3_ENDPOINT=https://beerpsrntgbrcklhqesj.storage.supabase.co/storage/v1/s3
SUPABASE_S3_REGION=ap-northeast-1
SUPABASE_S3_ACCESS_KEY_ID=
SUPABASE_S3_SECRET_ACCESS_KEY=
LOCAL_STORAGE_DIR=./storage_uploads

# Google Gemini AI
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash

# Cloudflare Workers AI (CLEF)
CLOUDFLARE_ACCOUNT_ID=20fdb67b6176cc01d24ed92c1850c729
CLOUDFLARE_API_TOKEN=
CLOUDFLARE_AI_GATEWAY_ID=default
CLEF_MODEL=@cf/cloudflare/clef

# AI Provider Selection
EXTRACTION_PROVIDER=local
DECISION_PROVIDER=gemini

# Email Service (Resend)
RESEND_API_KEY=
EMAIL_FROM=onboarding@resend.dev

# Frontend & CORS
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,https://ygsupa.netlify.app

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

## D. Local Run Commands

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

## E. Verification Checklist

- [ ] `/health` returns `{"status": "ok"}` at `http://localhost:8000/health`.
- [ ] Login page displays at `http://localhost:5173/login`.
- [ ] 1-Click login as **Reviewer** (`reviewer@example.com` / `Password123!`) works.
- [ ] 1-Click login as **Business Owner** (`business@example.com` / `Password123!`) works and displays scoped dashboard.
- [ ] Dashboard displays status metric cards, overdue alert banner, and recent request table.
- [ ] Controls tab lists `C001`, `C002`, `C003`, and `C004`.
- [ ] Scopes tab displays target scopes (`IT Operations Team`, `Finance Team`, `Jai Ram`, etc.).
- [ ] Public Submission portal loads via `http://localhost:5173/submit/demo-token-itops-2026-0001`.
- [ ] Uploading `sample_evidence/Complete_Access_Review_Q3_2026.pdf` produces `COMPLETE` status and positive audit findings.
- [ ] Uploading `sample_evidence/Incomplete_User_Roster.xlsx` produces `INCOMPLETE` status and lists missing requirements.
- [ ] APScheduler triggers reminders and logs communication events.
- [ ] Audit logs reflect all actions in `http://localhost:5173/audit-logs`.
