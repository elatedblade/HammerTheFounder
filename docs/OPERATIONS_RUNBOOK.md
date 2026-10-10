# HTF operations and deployment runbook

## Local startup

Copy `.env.example` to `.env` only if no `.env` exists; never overwrite existing
credentials. Fill the required Clerk configuration privately. Then:

```sh
docker compose up -d --build
docker compose exec backend python manage.py migrate --noinput
```

Candidate: `http://localhost:3000`; operators: `http://localhost:3001`; API:
`http://localhost:8000`. Development images do not hot-reload host edits: rebuild
the affected service. No live messages, payments or AI requests occur at startup.

### Clerk CLI setup in this monorepo

Authenticate with `clerk auth login` in the host terminal. The root is a Django/
Next monorepo rather than a single detectable frontend: run framework-specific
Clerk commands from `client-web` and `admin-web`, always targeting the selected
existing application. Do not scaffold a replacement app at the repository root.

Clerk writes frontend keys to each app's ignored `.env.local`. For Docker, pull
the same development keys into the ignored root `.env` using `clerk env pull
--app APP_ID --instance dev --file ../.env` from a frontend directory. Never print
or commit those files. Set `NEXT_PUBLIC_AUTH_MODE=clerk`; Django also needs the
matching `CLERK_ISSUER_URL` and `CLERK_JWKS_URL` (the issuer's
`/.well-known/jwks.json`). An audience is optional unless explicitly configured
in the instance's tokens. Do not retain an old public-key override for another app.

Next 16 uses `src/proxy.ts`, with the `/__clerk/:path*` matcher immediately after
the API matcher and protected `/workspace` routes. A single provider lives inside
the document body. Sign-in and sign-up pages are `/sign-in` and `/sign-up`; creating
an account never grants an HTF operational role. `CLERK_SECRET_KEY` is provided
only to Next server runtime, never as a public variable or Docker build argument.

For the existing backend identity adapter, configure development session claims
`email: {{user.primary_email_address}}` and
`phone_number: {{user.primary_phone_number}}`. Missing phone values are not invented.
Run `clerk doctor` from both frontends. Production-instance and shell-completion
warnings do not prevent development sign-in. Verify the first signup in the browser;
a passing CLI check alone does not establish that a user signed in successfully.

## First administrator and operator roles

Sign in once through Clerk so the corresponding local user exists. Confirm the
exact Clerk subject in your identity console. Infrastructure access is required
for these commands; knowing a subject is not authority to grant roles.

```sh
docker compose exec backend python manage.py set_htf_role \
  --subject CLERK_SUBJECT --role SUPERADMIN --bootstrap --reason 'Initial platform owner'
docker compose exec backend python manage.py set_htf_role \
  --subject OPERATOR_SUBJECT --role OPERATOR --actor ADMIN_SUBJECT --reason 'Approved operations access'
```

Bootstrap refuses to run when an active administrator already exists. Subsequent
grants require an active administrator actor; only superadmins manage superadmin
roles. The last active superadmin cannot be demoted. Role changes are audited.
This is an infrastructure-admin command, not a public role-assignment API.

## Run a manual campaign

1. Candidate signs in, saves intake and uploads a resume.
2. Operator reviews candidate facts and the resume; optionally queues parsing.
3. Approve the profile or request changes with notes. Approval requires profile
   basics and a verified uploaded resume.
4. Create campaign, select its plan and trial metadata. Admin assigns an operator.
5. Start the ready campaign. Operators see assigned campaigns and unassigned
   intake; unrelated active campaigns are inaccessible.
6. Create/select company and job, then record an application. Source identity,
   canonical URL and candidate/job uniqueness prevent common duplicates.
7. Work the generated review tasks. Submit externally **manually**, then record
   the transition. Failures require notes; interviews can be scheduled with an
   explicit future date/time.
8. For outreach, create/select contact, check suppression, prepare/review the
   message, send externally manually, then record SENT and later outcomes.
9. Candidate dashboard reads scoped records and server-side aggregates.
10. Record a pending payment. An administrator verifies the receipt reference;
    no payment provider is called and recording a payment does not charge anyone.

Plan restrictions apply when recording external execution: application submission
requires an ACTIVE application-enabled campaign; outreach SENT requires an ACTIVE
outreach-enabled campaign. Closing campaigns prevents further operational writes.

## Customer communications and AI

- `RESEND_API_KEY` and `RESEND_FROM_EMAIL` enable explicit transactional email
  dispatch. Recipient must match the campaign customer's saved email. Resend is
  never the cold-outreach execution engine. Keep the sending domain verified.
- WhatsApp remains manual. Draft/mark-sent validates the saved customer's phone.
  Configure Clerk token claims for `email` and `phone_number` if needed; HTF does
  not infer or fabricate missing identity contact details.
- `UPI_ID`, `UPI_PAYEE_NAME`, `UPI_INSTRUCTIONS` populate payment instructions.
  Missing details show an unavailable state; no fabricated QR/payment destination.
- `OMNIROUTE_BASE_URL` (including `/v1`), `OMNIROUTE_API_KEY`, `OMNIROUTE_MODEL`
  enable PydanticAI structured proposals. The gateway must support OpenAI native
  JSON-schema output. Each run has one bounded request, no tools, no automatic
  external actions, and no silent retries that could incur duplicate cost.
- AI input is a source reference: `resume_id`, `job_id`, `contact_id`, or QA
  `content`. Canonical candidate facts are loaded server-side. Outputs require
  human review and are never automatically applied.
- AI source versions, agent/prompt versions, latency and tokens are recorded.
  Currency cost is not invented: configure provider pricing outside this release
  before treating usage as a financial cost report.

## Private resume storage

Set the four AWS variables in `.env.example`; enable bucket Block Public Access,
TLS-only access and encryption. Grant the backend only required object GET/HEAD/PUT
permissions on the candidate prefix. Never make resumes public.

Browser upload also requires an S3 bucket CORS policy, independent of Django CORS:

```json
[{"AllowedOrigins":["https://candidate.example.com"],"AllowedMethods":["PUT"],"AllowedHeaders":["content-type"],"MaxAgeSeconds":300}]
```

Use exact development origins when testing locally. Authorizations expire after
five minutes. Completion checks size/type metadata; this is **not malware scanning**.
Downloads are authorized separately and returned with no-store cache headers.
PDF/DOCX parsing is bounded; legacy DOC stays downloadable but is explicitly
unsupported for parsing. Image-only PDFs report that OCR is required. Extracted
text is operational-only and the preview is capped at 32,000 characters.

## Production deployment

`compose.production.yml` is a separate topology, not an overlay on development.
It uses Gunicorn and non-root Next standalone servers. PostgreSQL/Redis have no
host ports; HTTP app ports bind to loopback for a host TLS reverse proxy. Volumes
are persistence, **not backups**. Cloud-provider provisioning is deliberately not
selected or executed by this repository.

Create a private `.env.production` from the environment template and supply:

- A unique random `DJANGO_SECRET_KEY` of at least 50 characters.
- Exact `DJANGO_ALLOWED_HOSTS`, HTTPS `CORS_ALLOWED_ORIGINS` and
  `CSRF_TRUSTED_ORIGINS`; public `NEXT_PUBLIC_API_URL` and Clerk public key.
- PostgreSQL credentials/`DATABASE_URL`; Redis service `REDIS_URL` and cache DB 1
  `CACHE_URL`. Use managed encrypted database credentials when deploying remotely.
- `TRUST_PROXY_SSL_HEADER=true` only when your trusted proxy strips incoming
  forwarded-protocol headers and sets `X-Forwarded-Proto` itself.
- `HTF_ENVIRONMENT=production`, optional release ID and Sentry DSNs.

For Railway, create separate services for the API, Celery worker, customer web,
and admin web. Use the matching files under `infra/railway/` as the service
configuration. The API service runs the migration pre-deploy command and uses
`/ready/` as its deployment health check; `/health/` remains a dependency-light
liveness endpoint. The worker has no public HTTP endpoint. Set
`DJANGO_SETTINGS_MODULE=config.settings.production` on both API and worker, and
set `CACHE_URL` explicitly on the API and worker using the Railway Redis
connection URL (with a separate logical database from the Celery broker when
supported).

The Railway TOML files are legacy Config-as-Code files and Railway has announced
their deprecation after 2026-12-01. They are retained as reproducible service
defaults for the current launch; migrate them to Railway Infrastructure as Code
before that deadline.

Public Next variables are compiled at build time; rebuild after changing them.
Never place private backend credentials in a `NEXT_PUBLIC_*` variable.

```sh
docker compose --env-file .env.production -f compose.production.yml build
docker compose --env-file .env.production -f compose.production.yml up -d postgres redis
docker compose --env-file .env.production -f compose.production.yml run --rm backend python manage.py migrate --noinput
docker compose --env-file .env.production -f compose.production.yml run --rm backend python manage.py check --deploy --fail-level WARNING
docker compose --env-file .env.production -f compose.production.yml up -d backend worker client-web admin-web
```

Before exposing traffic, configure TLS, edge rate/body limits, trusted proxy
headers, Clerk production origins, S3 CORS, private network/firewall policy,
encrypted backups and deployment rollback. Validate CSP against the actual Clerk
and asset origins before enforcing it; do not copy a permissive wildcard CSP.
The backend has shared Redis-backed soft rate limits and no-store API responses.
These are not a replacement for edge abuse protection or a security assessment.

`/ready/` checks PostgreSQL and the configured cache/Redis connection and returns
503 with only safe check names when either dependency is unavailable. It is for
deployment readiness, not continuous uptime monitoring. Configure an external
uptime monitor separately if continuous monitoring is required.

Sentry is opt-in: backend/worker and browser runtime errors are scrubbed of request
bodies, user context, breadcrumbs and error messages. Local variables, replay and
tracing are disabled. Source maps and Next server-runtime monitoring require an
explicit deployment integration; no telemetry is transmitted without a DSN.

## Worker and trial operations

Keep one or more Celery workers running. Monitor queue age, task failures and
`UNKNOWN` email delivery. Enqueue failures become persisted failure states rather
than fake success. Broker/result Redis must be private and persistent.

```sh
docker compose exec backend python manage.py expire_trials --limit 500
docker compose exec backend python manage.py reconcile_support_jobs --age-minutes 30
```

Trial dates remain valid through the end date in `HTF_TIME_ZONE` (default
Asia/Kolkata). Expiry pauses unpaid active campaigns and marks PAST_DUE; it never
charges customers or sends reminders. No recurring schedule is silently created.
Until an approved scheduler calls the expiry task, an operator runs this command.

Reconciliation marks interrupted AI/parser jobs failed and uncertain email
deliveries UNKNOWN. It never retries external actions. Before creating a new
email draft, inspect the provider using the stable notification idempotency key;
do not assume an interrupted worker means the provider did not accept the email.

## Backups, restore and rollback

Configure encrypted database backups outside the application image, with documented
retention, recovery-point objectives and restore drills. Example manual snapshot:

```sh
docker compose --env-file .env.production -f compose.production.yml exec -T postgres \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > /secure-backups/htf.dump
```

The backup contains personal data. Keep it outside git, encrypt it, restrict access,
and validate it in an isolated restore database using `pg_restore --exit-on-error`.
Never test a restore over production. Use S3 versioning/lifecycle policies consistent
with candidate retention and deletion obligations; do not leave abandoned uploads
indefinitely without an explicit retention policy.

For a bad release, stop traffic/writes first, assess migration compatibility, then
redeploy the last verified image. Do not blindly reverse migrations after new data
has been recorded. Retain application events and audit entries; application APIs
provide no delete/edit endpoints for audit records, but database administrators
still have database authority. Stronger tamper resistance requires DB policy and
off-host audit retention.

## Launch acceptance (requires configured services)

- Two real candidate accounts cannot access each other's profile, resumes,
  applications, outreach, events, payments or notifications.
- An unassigned operator cannot access another operator's active campaign.
- Real Google/Clerk sign-in, upload, object verification and authorized download
  work from the intended frontend origins.
- The full manual application/outreach journey renders on both frontends.
- Explicit Resend and OmniRoute staging requests succeed and failure states are
  recoverable; no test sends customer messages.
- Trial expiry, worker interruption and a database backup restore are rehearsed.
- Dependency/security review, privacy/retention policy, and appropriate malware
  scanning controls are agreed before accepting production candidate documents.

## Production dependency and privacy gates

Backend runtime and development dependencies are pinned with hashes in
`backend/requirements.lock` and `backend/requirements-dev.lock`. Frontend
dependencies use their committed npm lockfiles. GitHub Actions runs tests,
production Django checks, npm auditing, and `pip-audit`; audit findings remain
visible as warnings until an owner reviews and resolves them.

At the time of this release review, the scanner reports a known advisory for the
pinned `pydantic-ai-slim==1.0.18` and a frontend `braces` advisory in the
development lint dependency chain. Do not use a forced dependency upgrade in
production. Upgrade each dependency in a separate tested change, or document
why the affected code path is not reachable in the deployed runtime.

Before accepting real candidate documents, the owner must publish and approve a
privacy notice, retention/deletion schedule, customer service/refund terms,
operator access policy, and an incident-response contact. This repository does
not claim that legal approval exists merely because technical storage and audit
controls are implemented.
