# Final Hackathon Submission

## LEAP Young Innovators Hackathon 2026

### Submission Checklist
- [x] Application code committed and tested
- [x] Full-stack application deployed and accessible online
- [x] README.md completed per LEAP Young Innovators Hackathon guidelines
- [x] Architecture diagrams and documentation provided under `docs/`
- [x] Automated test suite passing (`pytest backend/tests/ -v`)
- [x] Dockerfile verified and deployable
- [x] Sensitive credentials purged from git history

### Project Metadata
- **Project Name**: LOD2 Evidence Bot (Autonomous Control Testing Platform)
- **Repository**: [https://github.com/DarshanHegdeP/YG-Hackathon.git](https://github.com/DarshanHegdeP/YG-Hackathon.git)
- **Target Branch**: `feature/supa`
- **Live Hosted Application**: [https://ygsupa.netlify.app/](https://ygsupa.netlify.app/)
- **Backend Deployment**: Render Web Service (FastAPI / Docker)
- **Problem Statement**: Automated Second Line of Defense (LOD2) Control Testing & Evidence Collection

### Key Technical Deliverables
1. **Frontend (React 18 + Vite + Tailwind CSS)**: Executive Reviewer dashboard, Business Owner scoped views, and tokenized public upload portals.
2. **Backend (FastAPI + SQLAlchemy 2.0)**: Asynchronous REST API with RBAC, document parser, in-process APScheduler, and cryptographic audit trail.
3. **Dual AI Decision Engine**: Google Gemini (1.5 Flash / 3.1 Flash-Lite) and Cloudflare Workers AI (CLEF model).
4. **Storage Architecture**: Supabase S3-compatible storage (`evidence` bucket) with Boto3 client and local disk fallback.
5. **Database**: PostgreSQL with connection pooling and zero-config SQLite local fallback.
