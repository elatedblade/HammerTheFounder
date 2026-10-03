---
name: api-design
description: Design REST or GraphQL APIs with complete specs, versioning, and documentation.
---

# API Design

Act as an API architect. Design a production REST (or GraphQL) API for
[PRODUCT/FEATURE].
Deliver:
1. Complete endpoint list with HTTP methods, paths, and purpose.
2. Request/response schemas (JSON) for every endpoint — include edge cases.
3. Pagination strategy (cursor-based preferred, explain why).
4. Filtering, sorting, and search query parameter conventions.
5. Versioning strategy (URL path, header, or query param — pick one, justify).
6. Error response format — standardized across all endpoints with error codes.
7. Rate limiting headers and behavior.
8. Authentication flow for each endpoint (public, authenticated, admin).
9. Idempotency strategy for POST/PUT/DELETE operations.
10. HATEOAS or resource linking approach.
11. OpenAPI/Swagger spec for the complete API.
12. SDK/client generation strategy.
Follow REST maturity model Level 3. Every endpoint must be idempotent-safe
or explicitly documented as non-idempotent. No verbs in URLs.
