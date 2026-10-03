---
name: performance-optimization
description: Audit and optimize frontend, backend, and database performance with measurable targets.
---

# Performance Optimization

Act as a performance engineer. Audit and optimize [PRODUCT/FEATURE].
Stack: [your stack].
Current pain points: [describe — slow pages, high latency, etc.].
Deliver:
1. Frontend performance:
   - Bundle size analysis and reduction plan.
   - Code splitting strategy (route-based, component-based).
   - Image optimization (formats, lazy loading, CDN).
   - Critical rendering path optimization.
   - Core Web Vitals targets: LCP < 2.5s, INP < 200ms, CLS < 0.1.
2. Backend performance:
   - Slow query identification and optimization (EXPLAIN ANALYZE).
   - N+1 query detection and fixes.
   - Connection pooling configuration.
   - Async processing — what to move off the hot path.
3. Database performance:
   - Index analysis — missing indexes, unused indexes.
   - Query plan optimization.
   - Read replica routing strategy.
4. Network:
   - CDN configuration.
   - Compression (gzip/brotli).
   - HTTP/2 or HTTP/3 setup.
   - API response payload optimization.
5. Benchmarks — define performance budgets per route/endpoint
   with specific millisecond targets.
Give me measurable before/after targets, not vague "make it faster."
