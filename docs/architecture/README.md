# Solution Architecture — LOD2 Evidence Bot

## High-Level Architecture Diagram

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

## Relational Entity Hierarchy

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
