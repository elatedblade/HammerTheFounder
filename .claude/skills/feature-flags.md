---
name: feature-flags
description: Implement feature flags with gradual rollouts, targeting, and A/B testing integration.
---

# Feature Flags & Rollouts

Act as a release engineer. Implement feature flags for [PRODUCT].
Deliver:
1. Feature flag system: build vs. buy (LaunchDarkly, Unleash, Flagsmith,
   custom) — justify.
2. Flag types: release toggle, experiment toggle, ops toggle, permission toggle.
3. Flag naming convention and lifecycle (create → enable → clean up).
4. Targeting: by user, by org, by %, by environment, by attribute.
5. Client-side vs. server-side evaluation — when to use each.
6. Default values and fallback behavior when flag service is down.
7. A/B testing integration — how flags connect to experiment analysis.
8. Gradual rollout strategy: 1% → 5% → 25% → 50% → 100% with metrics
   gates at each stage.
9. Kill switch pattern — instant disable for any feature in production.
10. Flag cleanup process — how to detect and remove stale flags.
11. Audit trail — who changed which flag when.
Never deploy a flag without a cleanup date. Stale flags are tech debt
that compounds silently.
