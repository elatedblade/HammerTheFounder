---
name: security-hardening
description: Audit and harden application security with OWASP Top 10 mitigations and exact configs.
---

# Security Hardening

Act as a penetration tester and AppSec engineer reviewing my product
before launch.
Stack: [your full stack — frontend, backend, DB, infra, third-party services].
Deliver a security audit covering:
1. OWASP Top 10 — go through each one, assess my app's risk, and give
   specific mitigations (not generic advice).
2. Input validation — every user input vector, what validation is needed,
   and where (client AND server).
3. SQL injection, XSS, CSRF, SSRF, IDOR — concrete attack scenarios
   against MY app and how to block each.
4. Secrets management — where secrets live, how they're rotated, what
   happens if a secret leaks.
5. Dependency vulnerability scanning setup.
6. Content Security Policy (CSP) headers — give me the exact header values.
7. CORS configuration — exact origins, methods, headers.
8. File upload security — type validation, size limits, malware scanning.
9. Data encryption — at rest and in transit, which algorithms, key management.
10. Security incident response playbook — step-by-step.
DO NOT give vague advice like "sanitize inputs." Give me exact code,
exact configs, exact header values.
