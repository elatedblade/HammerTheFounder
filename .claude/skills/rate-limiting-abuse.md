---
name: rate-limiting-abuse
description: Implement rate limiting and abuse prevention with distributed algorithms and bot detection.
---

# Rate Limiting & Abuse Prevention

Act as a platform security engineer. Implement rate limiting and abuse
prevention for [PRODUCT].
Deliver:
1. Rate limiting strategy per endpoint:
   - Public endpoints: strict (e.g., 10/min for login, 100/min for reads).
   - Authenticated endpoints: moderate (e.g., 1000/min).
   - Admin/internal: relaxed or unlimited.
2. Algorithm choice: token bucket, sliding window, fixed window — justify.
3. Implementation: middleware, API gateway, or both.
4. Rate limit headers: X-RateLimit-Limit, Remaining, Reset.
5. Response on limit: 429 with Retry-After header.
6. Distributed rate limiting (Redis-backed) for multi-instance deploys.
7. Bot detection: CAPTCHA triggers, behavioral analysis, fingerprinting.
8. Abuse patterns to detect: credential stuffing, scraping, spam
   submissions, API abuse.
9. IP-based vs. user-based vs. API-key-based limiting — when to use each.
10. Allowlist/blocklist management — IP ranges, user agents, API keys.
11. DDoS mitigation — CDN-level (Cloudflare/AWS Shield) + application-level.
Assume every public endpoint WILL be abused. Design for it from day one.
