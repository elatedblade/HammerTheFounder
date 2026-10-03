---
name: database-design
description: Design database schemas, indexing strategies, and data modeling for scale.
---

# Database Design & Modeling

Act as a database architect for a production system.
Domain: [describe your domain — e.g., e-commerce, SaaS, social platform].
Deliver:
1. Full ER diagram with all entities, relationships, and cardinalities.
2. Table schemas with columns, types, constraints, NOT NULLs, defaults.
3. Indexing strategy — which columns, why, composite indexes, partial indexes.
4. Normalization decisions — where you normalized and where you intentionally
   denormalized for performance (with justification).
5. Soft delete vs hard delete strategy per entity.
6. Audit trail / history tracking approach.
7. Multi-tenancy strategy (if applicable): row-level, schema-level, or DB-level.
8. Migration strategy: how to evolve schema without downtime.
9. Read replicas, sharding, or partitioning plan for scale.
10. Seed data and test data generation scripts.
Use [PostgreSQL / MySQL / MongoDB — specify]. Assume the DB will hold
100M+ rows within 2 years. Every decision must include the trade-off.
