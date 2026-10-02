# ADR 0002: Use PostgreSQL as the system of record

## Context

Campaign, application, outreach, billing, and audit state require relational
constraints, transactions, and reliable querying across modules.

## Decision

Use PostgreSQL for all durable business state. Development and CI use
PostgreSQL-compatible configuration rather than treating SQLite as a substitute
for the application's database contract.

## Alternatives

- Use SQLite for development and tests.
- Use a document database as the primary store.

## Consequences

The application exercises the production database behavior earlier and gains
strong constraints and transactional consistency. Local setup requires a
PostgreSQL service, increasing setup cost slightly.
