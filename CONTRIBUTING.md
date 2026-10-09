# Contributing Guidelines

## LEAP Young Innovators Hackathon 2026

Thank you for contributing to the **LOD2 Evidence Bot** project!

### Development Workflow
1. **Branching**: Create feature branches from `main` (e.g., `feature/document-parser`, `fix/ai-validation`).
2. **Secrets & Security**: Never commit `.env` or sensitive credentials. Use `backend/.env.example` and `frontend/.env.example`.
3. **Automated Testing**: Ensure automated tests pass prior to merging (`pytest backend/tests/ -v`).
4. **Code Quality**: Follow standard Python (PEP 8) and React JavaScript ES6+ conventions.
