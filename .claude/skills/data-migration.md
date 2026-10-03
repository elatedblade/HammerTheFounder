---
name: data-migration
description: Design database migration strategies with zero-downtime patterns and rollback plans.
---

# Data Migration & Versioning

Act as a database migration specialist. Design a migration strategy for
[PRODUCT].
Deliver:
1. Migration tool setup (Flyway / Alembic / Knex / Prisma Migrate — justify).
2. Migration naming convention and versioning scheme.
3. Zero-downtime migration patterns:
   - Add column → backfill → make non-null → drop old.
   - Expand-and-contract pattern for schema changes.
4. Rollback strategy — every migration must have a reversible down migration.
5. Data backfill scripts — idempotent, batchable, resumable.
6. Testing migrations — against production-like data volumes.
7. CI integration — auto-run pending migrations in staging.
8. Production migration runbook — pre-checks, execution, verification, rollback.
9. Seed data management — separate from migrations.
10. Schema drift detection — how to catch manual DB changes.
Never run ALTER TABLE on a 100M-row table without testing on a copy first.
Never deploy code that depends on a migration before the migration has run.
