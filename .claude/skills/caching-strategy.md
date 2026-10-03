---
name: caching-strategy
description: Design multi-layer caching with invalidation strategies for performance at scale.
---

# Caching Strategy

Act as a caching architect. Design a multi-layer caching strategy for
[PRODUCT].
Data patterns: [describe — read-heavy, write-heavy, real-time, etc.].
Deliver:
1. Cache layers: browser → CDN → application → database query cache.
   For each layer: what to cache, TTL, invalidation strategy.
2. Cache key design — naming convention, namespacing, versioning.
3. Invalidation strategy per entity:
   - Time-based (TTL)
   - Event-based (write-through, write-behind)
   - Manual purge
4. Cache stampede prevention (locking, probabilistic early expiration).
5. Hot key handling.
6. Cache warming strategy for cold starts.
7. Redis/Memcached configuration — eviction policy, memory limits,
   persistence settings.
8. HTTP caching headers per route: Cache-Control, ETag, Last-Modified
   — exact values.
9. Cache hit ratio targets and monitoring.
10. What NOT to cache — and why.
Every cache must have a documented invalidation path. "Cache and pray"
is not a strategy.
