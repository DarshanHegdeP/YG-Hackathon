# System Architecture — AI-Powered Evidence Collection Bot (LOD2 Evidence Platform)

## 1. High-Level System Architecture

```
                  ┌────────────────────────────────────────────────────────┐
                  │                    React 18 UI                         │
                  │           (Vite + Tailwind CSS + Axios)                │
                  │   ├── Reviewer View (/controls, /scopes, /audits)      │
                  │   ├── Business Owner Scoped View (/reviews, /requests) │
                  │   └── Public Submission Portal (/submit/:secureToken)  │
                  └───────────────────────────┬────────────────────────────┘
                                              │ HTTPS / REST (JSON & Multipart)
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │                 FastAPI Backend                        │
                  │   ├── Router Layer (Auth, Controls, Evidence, etc.)    │
                  │   ├── Role-Based Access Control (RBAC Deps)            │
                  │   ├── Document Parser (PDF, XLSX, DOCX, CSV)           │
                  │   ├── Storage Service (S3 boto3 / Supabase / Local)    │
                  │   ├── Dual AI Routing Engine (Gemini / Cloudflare CLEF)│
                  │   └── In-Process APScheduler (Background Reminders)    │
                  └───────────┬───────────────┬────────────────┬───────────┘
                              │               │                │
                   PostgreSQL │          REST │           REST │
                  (Supabase / │               ▼                ▼
                   Local DB)  │        ┌─────────────┐  ┌─────────────┐
                              │        │ Google AI   │  │ Cloudflare  │
                              │        │ (Gemini)    │  │ (CLEF Model)│
                              │        └─────────────┘  └─────────────┘
                              ▼               │
                  ┌─────────────────────┐     │ REST
                  │ Supabase S3 Storage │     ▼
                  │  (Bucket: evidence) │  ┌─────────────┐
                  │ (Local FS Fallback) │  │ Resend API  │
                  └─────────────────────┘  │ (Email Svc) │
                                           └─────────────┘
```

---

## 2. Core Business Entity Hierarchy

```
Organization
  └── Scopes (PERSON, TEAM, DEPARTMENT, APPLICATION, SYSTEM_OWNER)
        └── Controls (Reusable definitions: e.g. C001, C002, C003, C004)
              └── Control Evidence Requirements (Checklist of mandatory/optional items)
                    └── Control Assignments (Mapping Scope ↔ Control ↔ Reviewer)
                          └── Reviews (Specific audit cycle with period dates & due date)
                                └── Evidence Requests (Submission token, request code, due date)
                                      ├── Evidence Files (Stored in Supabase S3, SHA-256 hashed)
                                      ├── AI Validations (Gemini / Cloudflare CLEF assessment findings)
                                      └── Communications (Sent reminders, missing notices, escalations)
```

---

## 3. Strict Architectural Boundary Principles

1. **PostgreSQL / Relational Database is the Authoritative Source of Truth**:
   All states (status of evidence requests, communications sent, file records, review cycles) are committed to relational tables. Application restarts do not lose reminder states or workflow progress.
   - Production / Hosted environment: **Supabase PostgreSQL** pooler auto-derived from project URL and secret key.
   - Local offline fallback: **SQLite** (`sqlite:///./evidence_bot.db`).

2. **AI Interprets; Backend Decides**:
   The AI (Google Gemini or Cloudflare Workers AI with CLEF) performs structured semantic audit analysis on extracted document text, returning a strictly typed JSON schema (`status`, `relevance`, `confidence`, `missingInformation`, `findings`, `reason`).
   - The AI **never** triggers emails directly.
   - The AI **never** alters permissions or user accounts.
   - The AI **never** decides system authorization.
   - The FastAPI backend validates the structured AI response, updates the request state deterministically, and triggers appropriate email workflows.

3. **Background Scheduling Without Redis or Celery**:
   To ensure lightweight, cost-effective, and container-friendly operations without external broker infrastructure, the system utilizes **APScheduler** (`BackgroundScheduler`).
   - The scheduler queries database rows for open requests.
   - Compares timestamps with configured due date offsets.
   - Checks the `communications` table to ensure **idempotency** (never sends duplicate reminder emails).

4. **Unified Triple-Tier Object Storage**:
   The backend implements `StorageService` with automatic failover across three tiers:
   - **Tier 1 (Primary)**: Supabase S3-compatible API using `boto3` (`SUPABASE_S3_ENDPOINT`, `SUPABASE_S3_REGION=ap-northeast-1`, bucket `evidence`).
   - **Tier 2 (Secondary)**: Supabase Storage SDK via `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
   - **Tier 3 (Local)**: Local filesystem directory (`./storage_uploads`).

5. **Cryptographic Integrity & Deduplication**:
   Every uploaded file is hashed using **SHA-256** prior to persistence. Duplicate submissions or corrupted uploads are identified and logged in the immutable audit trail.

---

## 4. Multi-Format Document Parsing Pipeline

```
Evidence Upload (PDF, XLSX, XLS, DOCX, CSV)
      │
      ├── 1. Binary validation & Size check (Max 25 MB)
      ├── 2. SHA-256 Checksum generation
      ├── 3. Storage persistence (Supabase S3 bucket / Local disk)
      │
      ▼
Document Extraction Service
      ├── PyMuPDF (fitz)   ─── Page-by-page text layout extraction
      ├── openpyxl/pandas  ─── Sheet names, column headers & rows normalization
      ├── python-docx      ─── Paragraph structure & tabular extraction
      └── pandas (CSV)     ─── Tabular rows serialization
      │
      ▼
Normalized Extracted Text (~35,000 characters context)
      │
      ▼
AI Decision Engine (Google Gemini 1.5 Flash / Cloudflare CLEF)
      │
      ├── If COMPLETE    ─── Request marked COMPLETE, Completion email sent
      └── If INCOMPLETE  ─── Request marked INCOMPLETE, Missing items email sent
```

---

## 5. Automated Reminder & Escalation State Machine

```
   [Initiate Review Cycle]
             │
             ▼
   [Initial Request Email Dispatched]
             │
             ├── 2 Days Before Due Date ──► [Reminder #1 Sent]
             │
             ├── 1 Day Before Due Date  ──► [Reminder #2 Sent]
             │
             ├── On Due Date            ──► [Final Urgent Reminder Sent]
             │
             └── Past Due Date (>1 Day) ──► [Escalation to Manager/Escalation Contact]
                                             (Status transitioned to OVERDUE)
```
