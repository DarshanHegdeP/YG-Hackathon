# System Architecture — AI-Powered Evidence Collection Bot

## 1. High-Level System Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │                 React UI                     │
                  │        (Vite + Tailwind CSS + Axios)         │
                  └──────────────────────┬───────────────────────┘
                                         │ HTTPS / REST (JSON)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │              FastAPI Backend                 │
                  │   ├── Router Layer (Auth, Controls, etc.)    │
                  │   ├── Authority Engine (Business Logic)      │
                  │   ├── Document Parser (PDF, XLSX, DOCX, CSV) │
                  │   └── In-Process APScheduler                 │
                  └──────────┬───────────┬───────────────┬───────┘
                             │           │               │
                  PostgreSQL │           │ REST          │ REST
                (Supabase /  │           │               │
                 Local DB)   │           ▼               ▼
                             │    ┌─────────────┐ ┌─────────────┐
                             │    │ Google AI   │ │ Resend API  │
                             │    │ (Gemini 1.5)│ │ (Email Svc) │
                             │    └─────────────┘ └─────────────┘
                             ▼
                  ┌─────────────────────┐
                  │  Supabase Storage   │
                  │ (Local FS Fallback) │
                  └─────────────────────┘
```

---

## 2. Core Business Entity Hierarchy

```
Organization
  └── Scopes (PERSON, TEAM, DEPARTMENT, APPLICATION, etc.)
        └── Controls (Reusable definitions: e.g. C001, C002)
              └── Control Evidence Requirements (Checklist of mandatory/optional items)
                    └── Control Assignments (Mapping Scope ↔ Control ↔ Reviewer)
                          └── Reviews (Specific audit cycle with period dates & due date)
                                └── Evidence Requests (Submission token, request code, due date)
                                      ├── Evidence Files (Stored in bucket, SHA-256 hashed)
                                      ├── AI Validations (Gemini assessment findings, confidence)
                                      └── Communications (Sent reminders, missing notices, escalations)
```

---

## 3. Strict Architectural Boundary Principles

1. **PostgreSQL / Database is the Authoritative Source of Truth**:
   All states (status of evidence requests, reminders sent, files recorded, review cycles) are committed to relational tables. Application restarts do not lose reminder states or workflow progress.

2. **AI Interprets; Backend Decides**:
   Google Gemini performs structured semantic audit analysis on extracted document text, returning a strictly typed JSON schema (`status`, `relevance`, `confidence`, `missingInformation`, `findings`, `reason`).
   - The AI **never** triggers emails directly.
   - The AI **never** alters permissions or user accounts.
   - The AI **never** decides system authorization.
   - The FastAPI backend validates the structured AI response, updates the request state deterministically, and triggers appropriate email workflows.

3. **Background Scheduling Without Redis or Celery**:
   To ensure lightweight, cost-effective, and container-friendly hackathon and production operations without external broker infrastructure, the system utilizes **APScheduler** (`BackgroundScheduler`).
   - The scheduler queries database rows for open requests.
   - Compares timestamps with configured due date offsets.
   - Checks the `communications` table to ensure **idempotency** (never sends duplicate reminder emails).

4. **Cryptographic Integrity & Deduplication**:
   Every uploaded file is hashed using **SHA-256** prior to persistence. Duplicate submissions or corrupted uploads are identified and logged in the immutable audit trail.

---

## 4. Multi-Format Document Parsing Pipeline

```
Evidence Upload (PDF, XLSX, XLS, DOCX, CSV)
      │
      ├── 1. Binary validation & Size check (Max 25 MB)
      ├── 2. SHA-256 Checksum generation
      ├── 3. Storage persistence (Supabase Storage bucket / Local disk)
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
Gemini Flash Validation Engine (Structured JSON Response)
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
Each transition checks past records in the `communications` table, ensuring exact single execution per phase.
