---
name: cicd-devops
description: Build CI/CD pipelines with GitHub Actions, deployment strategies, and environment management.
---

# CI/CD & DevOps

Act as a DevOps engineer. Build a complete CI/CD pipeline for [PRODUCT].
Stack: [your stack].
Hosting: [cloud provider / platform].
Team size: [N engineers].
Deliver:
1. Git branching strategy (trunk-based, GitFlow, or GitHub Flow — justify).
2. CI pipeline (GitHub Actions / GitLab CI / etc.):
   - Lint → type-check → unit test → integration test → build → security scan
   - Exact YAML config file for the pipeline.
   - Parallelization and caching strategy for speed.
3. CD pipeline:
   - Staging auto-deploy on merge to main.
   - Production deploy: manual approval or auto with canary.
   - Blue-green or canary deployment strategy.
   - Rollback procedure — automated and manual.
4. Environment management: dev → staging → production.
   - Environment variable management (secrets, configs).
   - Database migration strategy per environment.
5. Docker:
   - Multi-stage Dockerfile optimized for size and security.
   - Docker Compose for local development.
6. Pre-commit hooks: lint, format, type-check, secret detection.
7. Release process: semantic versioning, changelog generation,
   GitHub releases.
8. Deployment SLA targets: deploy frequency, lead time, MTTR.
Pipeline must run in under 10 minutes. Every merge to main must be
deployable.
