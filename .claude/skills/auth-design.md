---
name: auth-design
description: Design authentication and authorization systems with RBAC/ABAC and security flows.
---

# Authentication & Authorization

Act as a security engineer specializing in identity. I need a complete
auth system for [PRODUCT].
User types: [list roles — e.g., admin, org owner, member, viewer, guest].
Deliver:
1. Auth flow diagrams for: signup, login, logout, password reset,
   email verification, OAuth/social login.
2. Token strategy: JWT vs. session — which and why, with token
   structure, expiry, and refresh flow.
3. RBAC or ABAC model — role definitions, permissions matrix, and
   how to check permissions in middleware.
4. Multi-tenancy auth: how org/workspace scoping works.
5. MFA implementation approach (TOTP, SMS, WebAuthn).
6. API key management for programmatic access.
7. Session invalidation strategy (logout from all devices, password change).
8. Account lockout and brute-force protection.
9. OAuth2/OIDC provider integration (Google, GitHub, etc.).
10. Security headers and CSRF/XSS protection in auth flows.
Assume attackers WILL try credential stuffing, session hijacking, and
privilege escalation. Design defensively.
