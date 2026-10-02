# ADR 0003: Use Celery with Redis for background work

## Context

Resume processing, AI work, notifications, and scheduled campaign tasks should
not block HTTP requests and must support retries and coordination.

## Decision

Use Celery workers with Redis as the broker and result backend. PostgreSQL
remains the source of truth; Redis is not used as the durable business store.

## Alternatives

- Execute long-running work synchronously in Django requests.
- Introduce a managed queue or event-streaming platform in v1.

## Consequences

Workers, retries, and asynchronous execution are available behind a familiar
Python interface. The system must operate and monitor Redis and keep tasks
idempotent.
