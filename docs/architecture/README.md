# Solution Architecture — LOD2 Evidence Bot

## High-Level Architecture Diagram

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

## Relational Entity Hierarchy

```
Organization
  └── Scopes (PERSON, TEAM, DEPARTMENT, APPLICATION, SYSTEM_OWNER)
        └── Controls (Reusable definitions: e.g. C001, C002, C003, C004)
              └── Control Evidence Requirements (Checklist of mandatory/optional items)
                    └── Control Assignments (Mapping Scope ↔ Control ↔ Reviewer)
                          └── Reviews (Specific audit cycle with period dates & due date)
                                └── Evidence Requests (Submission token, request code, due date)
                                      ├── Evidence Files (Stored in Supabase S3 bucket, SHA-256 hashed)
                                      ├── AI Validations (Gemini / Cloudflare CLEF assessment findings)
                                      └── Communications (Sent reminders, missing notices, escalations)
```
