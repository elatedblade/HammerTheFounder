---
name: error-resilience
description: Design error handling, retry strategies, and resilience patterns for production systems.
---

# Error Handling & Resilience

Act as an SRE designing error handling for a production system.
Deliver:
1. Error taxonomy — categorize all errors (validation, auth, not found,
   conflict, internal, upstream dependency, timeout).
2. Standardized error response format (JSON) with: code, message,
   details, request_id, documentation_url.
3. Error code registry — unique codes per error type, documented.
4. Exception hierarchy — base classes, custom exceptions, when to use each.
5. Retry strategy — which errors are retryable, backoff algorithm,
   max retries, jitter.
6. Circuit breaker pattern — for which dependencies, thresholds,
   half-open behavior.
7. Timeout strategy — per-dependency timeout values with justification.
8. Graceful degradation plan — what works when each dependency is down.
9. Dead letter queue — for failed async operations.
10. User-facing error messages — never expose internals, always actionable.
11. Global exception handler middleware — catch-all with logging.
No silent failures. Every error must be logged, categorized, and either
recovered from or surfaced to the user with a clear next step.
