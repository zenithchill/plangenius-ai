# Security Policy

PlanGenius AI adheres to industry-standard security practices for GenAI applications, client-server data hygiene, and privacy.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Architecture & Best Practices

1. **Zero Secret Leakage**:
   - No API keys, credentials, or private access tokens are stored or committed into the repository or source tree.
   - All credentials use standard `.env` configuration on the server side and browser `localStorage` in static client-side mode with user-revocable storage.
2. **Input Sanitization & Injection Prevention**:
   - All user inputs (event titles, prompts, guest counts, budgets) are strictly validated and type-checked before processing.
   - JSON payloads are capped at 2 MB to prevent Denial-of-Service (DoS) buffer attacks.
3. **HTTP Security Headers**:
   - `X-Content-Type-Options: nosniff` to prevent MIME-sniffing.
   - `X-Frame-Options: SAMEORIGIN` to mitigate clickjacking.
   - `X-XSS-Protection: 1; mode=block` for reflected cross-site scripting mitigation.
   - Content-Security-Policy (CSP) headers applied across all served web views.
4. **CORS & Least Privilege**:
   - REST endpoints reject non-whitelisted cross-origin methods and validate content types strictly.

## Reporting a Vulnerability

If you discover a security vulnerability in PlanGenius AI, please do not file a public issue. Instead, report it privately:

- **Email**: `sudhanshusharma30544@gmail.com`
- **Response SLA**: Initial triage within 24 hours; security fix release within 72 hours.
- **Disclosure Policy**: Coordinated disclosure following standard patch verification.
