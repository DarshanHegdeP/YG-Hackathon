# 🛡️ LOD2 Evidence Bot — System Architecture & Solution Guide
### Autonomous Control Testing & AI-Powered Evidence Collection Platform

[![Live Demo](https://img.shields.io/badge/Live_Demo-ygsupa.netlify.app-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)](https://ygsupa.netlify.app/)
[![Frontend Netlify](https://img.shields.io/badge/Frontend-Netlify-00C7B7.svg?style=flat-square&logo=netlify&logoColor=white)](https://ygsupa.netlify.app/)
[![Backend Render](https://img.shields.io/badge/Backend-Render-46E3B7.svg?style=flat-square&logo=render&logoColor=white)](https://render.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2+-61DAFB.svg?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-1.5_Flash-8E75B2.svg?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com)
[![Cloudflare CLEF](https://img.shields.io/badge/Cloudflare_AI-CLEF_Model-F38020.svg?style=flat-square&logo=cloudflare&logoColor=white)](https://developers.cloudflare.com/workers-ai/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

---

## 🌐 Live Production Deployment

| Component | Platform | Configuration / URL |
| :--- | :--- | :--- |
| **Frontend Web Application** | **Netlify** | [👉 https://ygsupa.netlify.app/](https://ygsupa.netlify.app/) |
| **Backend API Service** | **Render** | Dockerized Web Service (Oregon region, port 10000, `/health` health check) |
| **Relational Database** | **Supabase / PostgreSQL** | Managed PostgreSQL with connection pooling & SQLite fallback |
| **Object Storage** | **Supabase S3 Storage** | S3-compatible bucket `evidence` (`ap-northeast-1`) with Boto3 client |
| **Primary AI Engine** | **Google Gemini** | `gemini-1.5-flash` / `gemini-3.1-flash-lite` |
| **Alternative AI Engine** | **Cloudflare Workers AI** | `@cf/cloudflare/clef` via Cloudflare AI Gateway |

---

## 1. High-Level Architecture

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
                  │   ├── Multi-Format Parser (fitz, pandas, docx, csv)    │
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
        └── Controls (Reusable definitions: e.g. C001, C002, C003)
              └── Control Evidence Requirements (Checklist of mandatory/optional items)
                    └── Control Assignments (Mapping Scope ↔ Control ↔ Reviewer)
                          └── Reviews (Specific audit cycle with period dates & due date)
                                └── Evidence Requests (Submission token, request code, due date)
                                      ├── Evidence Files (Stored in Supabase S3, SHA-256 hashed)
                                      ├── AI Validations (Gemini / CLEF assessment findings, confidence)
                                      └── Communications (Sent reminders, missing notices, escalations)
```

---

## 3. Strict Architectural Boundary Principles

1. **PostgreSQL / Relational Database is the Authoritative Source of Truth**:
   All states (status of evidence requests, communications sent, file records, review cycles) are committed to relational tables. Application restarts do not lose reminder states or workflow progress.
2. **AI Interprets; Backend Decides**:
   The AI (Google Gemini or Cloudflare CLEF) performs structured semantic audit analysis on extracted document text, returning a strictly typed JSON schema:
   ```json
   {
     "status": "COMPLETE" | "INCOMPLETE" | "IRRELEVANT",
     "relevance": "HIGH" | "MEDIUM" | "LOW",
     "confidence": 0.94,
     "missingInformation": ["Exception Report", "Approval Evidence"],
     "findings": ["Active Directory user roster audited with 42 user accounts"],
     "reason": "The submitted evidence covers account listings but lacks required manager approval signoff."
   }
   ```
   - The AI **never** triggers emails directly.
   - The AI **never** alters permissions or user accounts.
   - The AI **never** decides system authorization.
   - The FastAPI backend validates the structured AI response, updates the request state deterministically, and triggers appropriate email workflows.
3. **Background Scheduling Without External Brokers**:
   To ensure lightweight, cost-effective, and container-friendly operations without external message brokers (no Redis or Celery), the system utilizes **APScheduler** (`BackgroundScheduler`).
   - The scheduler queries database rows for open requests.
   - Compares timestamps with configured due date offsets.
   - Checks the `communications` table to ensure **idempotency** (never sends duplicate reminder emails).
4. **Unified Triple-Tier Object Storage**:
   The `StorageService` attempts persistence in order:
   - **Tier 1**: Supabase S3-compatible API via `boto3` (`SUPABASE_S3_ENDPOINT`).
   - **Tier 2**: Supabase Storage client via `supabase-py` (`SUPABASE_URL`).
   - **Tier 3**: Local filesystem directory (`./storage_uploads`).
5. **Cryptographic Integrity & Non-Repudiation**:
   Every uploaded file is hashed using **SHA-256** prior to storage. Duplicate submissions or corrupted uploads are identified and logged in the immutable audit trail.

---

## 4. Multi-Format Document Parsing Pipeline

```
Evidence Upload (PDF, XLSX, XLS, DOCX, CSV)
      │
      ├── 1. Binary validation & Size check (Max 25 MB)
      ├── 2. SHA-256 Checksum generation
      ├── 3. Storage persistence (Supabase S3 bucket 'evidence' / Local disk)
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
AI Validation Engine (Routing: Gemini or Cloudflare CLEF)
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
