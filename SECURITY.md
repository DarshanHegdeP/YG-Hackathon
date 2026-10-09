# Security Policy

## LEAP Young Innovators Hackathon 2026

### Mandatory Security Principles
1. **No Sensitive Data or Production Secrets**: Never commit real production secrets, private keys, API credentials, customer PII, or internal tokens to this repository. All environment variables must be stored in uncommitted `.env` files using `.env.example` as a template.
2. **Cryptographic Standards**: Passwords must be hashed using industry-standard salted hashing (Bcrypt). JWT tokens must be signed using secure secrets and verified with standard algorithms (HS256).
3. **Least Privilege**: Role-based access control (RBAC) separates administrative, reviewer, and submitter permissions.
4. **Input Validation**: All API inputs, file types, and file sizes are strictly validated on the backend. Files uploaded to the evidence service are capped at 25MB and verified with SHA-256 checksums.
5. **Safe AI Integrations**: AI model prompts use strict temperature settings and read-only context buffers without direct execution privileges or unauthorized write permissions to the database.

### Vulnerability Reporting
If you identify any security vulnerability or issue in this prototype, please report it directly to the repository maintainers or hackathon organizers.
