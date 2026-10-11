# Production readiness record

This document describes the repository-side production controls for HTF. It is
not a legal, security-audit, provider-certification, or deployment approval.

## Deployment topology

Railway should run four application services plus managed PostgreSQL and Redis:

| Service | Configuration | Exposure | Process |
| --- | --- | --- | --- |
| API | `infra/railway/api.toml` | Public | Gunicorn + Django |
| Worker | `infra/railway/worker.toml` | Private | Celery worker |
| Customer web | `infra/railway/customer.toml` | Public | Next standalone server |
| Admin web | `infra/railway/admin.toml` | Public but authenticated | Next standalone server |

The API owns migrations through its Railway pre-deploy command. Do not run
migrations independently from every web or worker replica.

## Required Railway variables

### API and worker

- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `DJANGO_SECRET_KEY` — unique, random, at least 50 characters
- `DJANGO_ALLOWED_HOSTS` — exact API host plus `healthcheck.railway.app`
- `DATABASE_URL` — Railway PostgreSQL connection string
- `REDIS_URL` — Celery broker/result connection
- `CACHE_URL` — Redis cache/rate-limit connection; no default is used in production
- `CLERK_ISSUER_URL` and `CLERK_JWKS_URL` or the approved public-key alternative
- Private S3 configuration: region, bucket and credentials/role
- Exact HTTPS `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`

Optional provider variables must be configured only after staging verification:
Resend, OmniRoute, Sentry, UPI and WhatsApp.

### Customer and admin web

Public build-time variables:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `NEXT_PUBLIC_AUTH_MODE=clerk`
- `NEXT_PUBLIC_ADMIN_URL` for the customer app
- Optional `NEXT_PUBLIC_SENTRY_DSN`

Server-only runtime variable:

- `CLERK_SECRET_KEY`

Never place backend secrets, S3 keys, database URLs or Clerk server keys in a
`NEXT_PUBLIC_*` variable.

## Health and dependency behavior

- `/health/` is liveness only and intentionally does not contact dependencies.
- `/ready/` checks PostgreSQL and the configured cache backend. It returns 200
  only when both are reachable and 503 otherwise.
- Railway health checks happen during deployment; configure separate continuous
  uptime monitoring.
- Redis carries Celery messages and shared cache/rate-limit counters. PostgreSQL
  remains the business system of record. S3 stores private resume bytes.

## Release procedure

1. Open a pull request and wait for CI tests, typechecks, builds, migration drift
   checks and dependency reports.
2. Deploy staging with isolated Clerk, S3, PostgreSQL and Redis resources.
3. Run `python manage.py migrate --noinput` through the deployment mechanism.
4. Run `python manage.py check --deploy --fail-level WARNING` with production-like
   variables.
5. Verify the real customer and operator journeys with test accounts.
6. Exercise worker restart/reconciliation and restore a database backup into an
   isolated database.
7. Deploy the reviewed commit to production and record the release ID.

## Known release gates

- Clerk production issuer/origins and authenticated browser acceptance are
  deployment-specific and cannot be verified from this repository alone.
- S3 CORS, private access, encryption, malware scanning and retention must be
  verified with the real bucket.
- Resend and OmniRoute require staging requests and provider-budget review.
- The dependency scanner currently surfaces a pinned Python AI-package advisory
  and a frontend development-tool advisory. These require a separate tested
  dependency upgrade or explicit risk acceptance; they are not silently ignored.
- Privacy notice, retention/deletion schedule, refund/service terms and incident
  ownership must be approved before real candidate documents are accepted.
