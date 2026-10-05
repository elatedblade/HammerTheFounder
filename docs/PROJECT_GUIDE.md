# Hammer The Founder — Project Guide

This is the working guide for developing, running, and using Hammer The Founder
(HTF). It describes the current implementation, not only the long-term product
plan. Update this file when a user-visible workflow, API contract, environment
variable, data model, or operational command changes.

Current delivery evidence is in `DELIVERY_STATUS.md`. Production setup, role
bootstrap, S3 CORS and worker recovery are in `OPERATIONS_RUNBOOK.md`.

Latest branch verification and merge blockers are recorded in
[`RESTORE_BRANCH_VERIFICATION.md`](RESTORE_BRANCH_VERIFICATION.md). The branch
`feature/restore-inquiries-frontend` passes fresh-database tests but has not been
merged into main: the old database upgrade and combined-source checks fail.
Use http://localhost:13000 (candidate) and http://localhost:13001 (admin) for
the isolated, empty-database test environment; see that report for run/stop commands.

### Latest customer pages and inquiries

The public `/` route describes services without collecting a candidate profile.
`/plans` handles plan choice/inquiries and Help; `/profile` handles profile and
resume edits; `/dashboard` shows actual campaign lifecycle and activity. Signed-out
visitors go through Clerk sign-in before protected pages. The legacy `/workspace`
route redirects into the customer dashboard. Choosing a plan records an inquiry;
it does not activate a campaign or grant operational privileges.

Admin Inquiries and Notifications are primary tabs again, alongside Outreach and
the core operational tabs. Overview scope controls do not globally filter unrelated
workspace tabs. The browser suite covers public navigation/mobile behavior; real
authenticated customer/operator acceptance remains separate.

## 1. What HTF does

HTF is a managed job-search operations platform. A candidate supplies profile
information and a resume. HTF operators use that information to run a search
campaign, record applications and outreach, and keep the candidate-facing
workspace current.

The product is manual-first in version one:

- PostgreSQL is the system of record.
- Candidates communicate with HTF through the web workspace and manual
  WhatsApp operations.
- Operators manually perform external job-search actions.
- AI may assist research, matching, drafting, or quality assurance, but does
  not autonomously submit external actions.
- The web applications and API enforce role and ownership boundaries; the
  frontend is never the authority for access control.

## 2. Current implementation

### Candidate experience

The client web app currently supports:

1. Clerk sign-in with a local Django identity lookup.
2. Candidate profile onboarding and later editing.
3. Draft and saved profile states with loading, retry, validation, and stale
   version conflict handling.
4. Target-role and preferred-location multi-select autocomplete fields. Users
   can select suggestions or enter custom values containing spaces and commas.
5. Resume metadata listing and upload authorization for PDF, DOC, and DOCX
   files up to 10 MB.
6. Direct browser-to-private-S3 upload followed by server-side object
   verification.
7. A read-only campaign workspace showing campaign status, plan, billing state,
   trial end date, and start date.
8. Complete structured intake: industries, compensation bounds, work authorization,
   sponsorship, notice period and additional preferences; read-only review state.
9. Server-derived overview, applications/outreach, interviews and scheduling dates,
   campaign activity, sent customer notifications, payment states and configured UPI instructions.
10. Authorized short-lived resume download links.

### Operations experience

The admin web app currently provides:

- Clerk sign-in.
- A role gate for `OPERATOR`, `ADMIN`, and `SUPERADMIN` accounts.
- Candidate review, resume download/parsing and parsed-text viewing.
- Campaign creation, assignment, settings and explicit lifecycle actions.
- Companies, jobs and applications, including interview scheduling and failure handling.
- Contacts, suppression, templates and manually recorded outreach/replies.
- Prioritized human review tasks with claiming and completion.
- Manual payment records and admin-only verification/refunds.
- Customer communication drafts, templates and explicit send/mark-sent actions.
- AI proposal requests grounded in saved candidate/job/contact/resume records.
- Server-derived metrics and campaign activity.

These workflows now have corresponding backend routes, migrations and UI.
Real Clerk/S3/Resend/OmniRoute verification still requires deployment-specific
configuration. See `DELIVERY_STATUS.md` for exact checks and remaining limits.
Operators can access assigned campaigns and unassigned intake campaigns;
only administrators change assignment and verify/refund payments.

## 3. Repository map

```text
.
├── backend/                 Django + DRF API and domain services
│   ├── config/              settings, URLs, auth, error handling, Celery
│   ├── apps/users/          local identity and role model
│   ├── apps/candidates/     candidate profile API and ownership policy
│   ├── apps/resumes/        resume metadata and upload-completion flow
│   ├── apps/campaigns/      campaign model, lifecycle, and visibility API
│   ├── apps/companies/       canonical company records
│   ├── apps/jobs/            normalized, deduplicated job records
│   ├── apps/applications/   application creation and status transitions
│   └── apps/integrations/   storage and authentication adapters
├── client-web/              candidate Next.js application
├── admin-web/               operator/admin Next.js operations workspace
├── docs/                    implementation plan, ADRs, and this guide
├── docker-compose.yml       PostgreSQL, Redis, backend, worker, and web apps
├── .env.example             redacted local configuration template
└── README.md                product overview and architecture reference
```

## 4. How the system works

```text
Candidate browser ── Clerk session ──┐
                                     ▼
                              Django REST API
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
             Candidate profile    Resumes          Campaigns
                    │                │                │
                    └────────────────┴────────────────┘
                                     ▼
                              PostgreSQL

Resume bytes: browser ── presigned PUT ── private S3 bucket
Background work: Django/Celery ── Redis broker ── worker
Operations UI: admin-web ── authenticated API ── operator/admin roles
```

### Request and authorization flow

1. Clerk authenticates the person in a Next.js application.
2. The frontend requests a bearer token and sends it to Django.
3. Django verifies the token through its configured Clerk/JWKS adapter and
   maps the external subject to the local `User` record.
4. DRF permissions check that the local user is active and has the required
   role.
5. Selectors scope objects to the authenticated user where ownership applies.
6. Domain services perform state changes and transactional validation.
7. PostgreSQL stores the resulting state; API responses use stable error
   envelopes for frontend branching.

The frontend may hide controls for convenience, but every API endpoint repeats
the authorization and ownership checks on the server.

## 5. Local setup

### Prerequisites

- Docker Desktop with Docker Compose.
- Node.js and npm for running frontend checks outside Docker.
- Python 3.10+ for running backend checks outside Docker.
- A Clerk development instance for an authenticated end-to-end browser flow.
- An AWS S3 bucket only if testing real resume uploads.

### First-time setup

From the repository root:

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend python manage.py migrate
```

The services are exposed at:

| Service | URL | Purpose |
|---|---|---|
| Candidate web | http://localhost:3000 | Candidate profile, resume, campaign view |
| Admin web | http://localhost:3001 | Operator/admin operations workspace |
| Django API | http://localhost:8000 | REST API |
| API health | http://localhost:8000/health/ | Dependency-light liveness check |
| PostgreSQL | localhost:5432 | Local relational database |
| Redis | localhost:6379 | Celery broker/result backend |

The local compose defaults are suitable for development only. They include
placeholder database credentials and a development Django secret; do not use
them in production.

### Clerk configuration

Set these values in `.env` and restart the web/backend services:

```dotenv
NEXT_PUBLIC_AUTH_MODE=clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
CLERK_ISSUER_URL=...
CLERK_JWT_AUDIENCE=...
CLERK_JWKS_URL=...
```

The exact issuer, audience, and JWKS values must match the Clerk development
instance. Never commit `.env`, Clerk secrets, JWTs, or private keys.

Without a Clerk publishable key, the candidate app deliberately shows its
authentication setup state rather than pretending that an authenticated flow
is available.

### Resume storage configuration

Resume storage is intentionally private. To enable real uploads, configure:

```dotenv
AWS_REGION=ap-south-1
AWS_S3_BUCKET=your-private-bucket
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

The bucket should have Block Public Access enabled. The API derives the object
key from the authenticated candidate and resume UUID, issues a short-lived
presigned `PUT` URL, and never accepts a client-provided S3 key. If these
settings are absent, the API returns `503 STORAGE_NOT_CONFIGURED` and creates
no resume record.

## 6. Candidate workflow

### Sign in and load the workspace

1. Open http://localhost:3000.
2. Sign in through Clerk.
3. The client calls `GET /api/v1/me/` to load the local HTF identity.
4. The client loads `GET /api/v1/candidate/profile/`.
5. A missing profile is represented as an empty editable draft; a saved profile
   is loaded from PostgreSQL.

### Edit and save the profile

The profile contains:

- Full name, headline, and current location.
- Experience summary.
- Target roles.
- Preferred locations.
- Remote preference.
- Target industries and expected compensation minimum/maximum (INR annual CTC).
- Work authorization, sponsorship requirement and notice period.
- Structured additional preferences and read-only operator review status.

Target roles and preferred locations are arrays in the API. In the UI, type
normally, choose a suggestion, press `Enter`, or type a comma to commit a tag.
Custom values are supported. The API validates the list shape, maximum of ten
items, trimming, length, and duplicate values.

Profile saves use optimistic versioning:

```text
PATCH /api/v1/candidate/profile/
{
  "full_name": "Ada Lovelace",
  "target_roles": ["Staff Engineer"],
  "preferred_locations": ["London, UK"],
  "profile_version": 2
}
```

The server increments `profile_version` on a successful save. A stale version
    returns `409 STALE_PROFILE_VERSION`; the UI offers a reload of the saved
server version instead of silently overwriting another edit.

### Upload a resume

The upload is a two-step application flow:

1. The client validates the extension, MIME type, non-zero size, and 10 MB
   limit.
2. The client sends metadata only to Django:

   ```text
   POST /api/v1/candidate/resumes/
   {
     "original_filename": "resume.pdf",
     "content_type": "application/pdf",
     "file_size": 248321
   }
   ```

3. Django creates a pending resume record and returns a short-lived signed PUT
   URL and required headers.
4. The browser sends the file bytes directly to S3; Django does not proxy the
   file.
5. The browser calls:

   ```text
   POST /api/v1/candidate/resumes/{resume_id}/complete/
   ```

6. Django performs a private S3 `HEAD` check for object existence, size, and
   content type. Only then is the record marked `UPLOADED`.

The metadata list is available from:

```text
GET /api/v1/candidate/resumes/
```

Resume endpoints are restricted to active `CLIENT` users and only return the
authenticated candidate's records. S3 keys and signed URLs are never included
in the metadata list.

### View campaign status

Candidates can read only their own campaigns:

```text
GET /api/v1/campaigns/
GET /api/v1/campaigns/{campaign_id}/
```

The client workspace displays the plan, lifecycle status, trial end date,
billing status, and start date. An empty list is a real state: HTF has not yet
created a campaign, rather than the UI inventing dashboard metrics.

## 7. Operator and administrator workflow

Open http://localhost:3001 and sign in with an active local user whose role is
`OPERATOR`, `ADMIN`, or `SUPERADMIN`. Client accounts are rejected by the
admin-web role gate and by backend permissions.

The current campaign API supports these operator/admin actions:

| Method | Endpoint | Result |
|---|---|---|
| `GET` | `/api/v1/campaigns/` | List visible campaigns |
| `POST` | `/api/v1/campaigns/` | Create a campaign for an active client profile |
| `GET` | `/api/v1/campaigns/{id}/` | Read one visible campaign |
| `POST` | `/api/v1/campaigns/{id}/start/` | Start a ready campaign or mark it onboarding |
| `POST` | `/api/v1/campaigns/{id}/pause/` | Move `ACTIVE` to `PAUSED` |
| `POST` | `/api/v1/campaigns/{id}/resume/` | Move `PAUSED` to `ACTIVE` |

Campaign creation example:

```json
{
  "candidate_id": 12,
  "plan": "NORMAL_APPLY",
  "trial_end_date": "2026-10-16",
  "settings_json": {"weekly_limit": 10}
}
```

Campaign creation is allowed only for active client profiles. A campaign is
created as `READY` when the candidate profile is complete, operator-approved and
at least one resume is verified as uploaded; otherwise it starts as `DRAFT`. Starting an
incomplete campaign moves it to `ONBOARDING` and returns
`409 CAMPAIGN_NOT_READY`. Starting a ready campaign moves it to `ACTIVE` and
sets `start_date` if it is not already set.

An administrator must assign an unassigned campaign before an operator can
start it. Administrators can start any visible ready campaign. Profile fact
edits reset review to `PENDING`; explicit review is required before starting.
PATCH `/campaigns/{id}/` updates plan/settings/trial and admin-only assignment.
POST `complete/` or `cancel/` closes a campaign and cancels outstanding tasks.

Lifecycle transitions are explicit rather than an unrestricted status PATCH:

```text
DRAFT ────────┐
ONBOARDING ───┼──> ACTIVE ──> PAUSED ──> ACTIVE
READY ────────┘
```

Invalid transitions return `409 INVALID_CAMPAIGN_TRANSITION`. Each successful
transition increments the campaign `version` and appends an actor-attributed
event and audit entry. Version numbers alone are not treated as audit history.

### Companies, jobs, and applications

These operational APIs are used by the admin workspace and restricted to
operators/admins unless noted otherwise:

| Method | Endpoint | Result |
|---|---|---|
| `GET` / `POST` | `/api/v1/companies/` | List or create canonical companies |
| `GET` / `PATCH` | `/api/v1/companies/{id}/` | Read or edit a company |
| `GET` / `POST` | `/api/v1/jobs/` | Filter or create normalized jobs |
| `GET` / `PATCH` | `/api/v1/jobs/{id}/` | Read or edit a job |
| `GET` | `/api/v1/applications/` | Read visible applications; operators can create |
| `POST` | `/api/v1/applications/{id}/transition/` | Move an application through its state graph |
| `GET` | `/api/v1/applications/{id}/` | Read one visible application |
| `GET` | `/api/v1/campaigns/{id}/applications/` | Read applications for a visible campaign |

Jobs are deduplicated by `(external_source, external_id)`. Applications are
deduplicated by `(candidate, job)`, with the candidate derived from the
campaign rather than trusted from the request. Application transitions are
explicit and include `DISCOVERED`, `SHORTLISTED`, `QUEUED`, `IN_PROGRESS`,
`SUBMITTED`, `IN_REVIEW`, `RECRUITER_CONTACTED`, `INTERVIEW`,
`INTERVIEW_SCHEDULED`, `OFFER`, and `REJECTED`, plus failure handling. The
service records `submitted_at` when an application enters `SUBMITTED`.

## 8. API and error conventions

All application routes are under `/api/v1/`. Authenticated requests use:

```http
Authorization: Bearer <Clerk-token>
```

Errors use this shape:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed.",
  "details": {}
}
```

Frontend code should branch on `code` or HTTP status, not scrape human-readable
messages. Common codes include:

| Code | Meaning |
|---|---|
| `UNAUTHENTICATED` | Missing or invalid authentication |
| `FORBIDDEN` | Authenticated user lacks the required role |
| `NOT_FOUND` | Resource is absent or outside the caller's visibility scope |
| `VALIDATION_ERROR` | Request fields are invalid |
| `STALE_PROFILE_VERSION` | Profile was saved from a stale version |
| `STORAGE_NOT_CONFIGURED` | Private S3 settings are incomplete |
| `CAMPAIGN_NOT_READY` | Candidate prerequisites are incomplete |
| `INVALID_CAMPAIGN_TRANSITION` | Requested lifecycle action is not allowed |

## 9. Data ownership and security rules

- Candidate profile, resume, and campaign reads are scoped by local user
  ownership unless the endpoint is explicitly an operator/admin operation.
- `candidate_id`, `campaign_id`, and S3 keys are never trusted as proof of
  ownership. The backend resolves and checks them.
- Only active `CLIENT` users can use candidate self-service profile and resume
  endpoints.
- Only active operational roles can create or transition campaigns.
- Private resume objects are accessed through short-lived signed URLs; no public
  resume URL is stored or returned.
- Secrets belong in `.env` or the deployment secret manager, never in source,
  documentation examples, logs, or test fixtures.
- PostgreSQL is authoritative; browser local storage is not used for profile or
  resume PII.

## 10. Testing and verification

Run checks from the repository root unless a command specifies a subdirectory.

### Backend checks

```bash
cd backend
python3 -m pytest -q
python3 manage.py check
python3 manage.py makemigrations --check --dry-run
```

The backend tests cover identity/permissions, candidate profile ownership and
version conflicts, resume validation/storage authorization/completion, and
campaign visibility and lifecycle transitions. Tests mock AWS at the storage
adapter boundary and never contact a real bucket.

### Frontend checks

```bash
cd client-web
npm run typecheck
npm run lint
npm run build

cd ../admin-web
npm run typecheck
npm run lint
npm run build
```

### Docker and smoke checks

```bash
docker compose up -d --build
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python -m pytest -q
curl -f http://localhost:8000/health/
curl -I http://localhost:3000/
curl -I http://localhost:3001/
```

For a browser smoke test, sign in at `http://localhost:3000`, edit a profile,
save and refresh it, add a resume if S3 is configured, and verify that the
campaign panel shows either the empty state or server-returned campaign data.
For the admin flow, sign in at `http://localhost:3001` with an operational
role and confirm that a client account receives the access-denied state.

## 11. Troubleshooting

### The old frontend is still visible

Rebuild the relevant service instead of relying on a stale image:

```bash
docker compose up -d --build client-web
```

Then hard-refresh `http://localhost:3000`.

### API requests fail with CORS errors

Ensure `CORS_ALLOWED_ORIGINS` contains the exact browser origins, normally:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

Restart the backend after changing `.env`.

### Authentication is unavailable

Check the Clerk publishable key and `NEXT_PUBLIC_AUTH_MODE`, then confirm the
backend issuer/audience/JWKS values. Restart both web and backend services.

### Resume upload says storage is not configured

This is an intentional setup state. Set all four AWS variables, keep the bucket
private, restart the backend, and retry. Do not work around it by making the
bucket public or sending file bytes through Django.

### A migration is missing

Run:

```bash
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py migrate
```

New migrations must be committed with the model change.

## 12. Documentation maintenance

When changing the project, update the smallest relevant documentation set in
the same change:

1. Update this guide when setup, usage, API behavior, data ownership, or
   troubleshooting changes.
2. Update `README.md` when the product scope or top-level architecture changes.
3. Add an ADR under `docs/adr/` when a durable architecture or provider choice
   changes.
4. Update `docs/IMPLEMENTATION_PLAN.md` when a milestone, definition of done,
   or future boundary changes.
5. Add or update tests for the user-visible behavior and list the exact checks
   in the change summary.

The guide must remain honest about what is implemented. Do not document a
placeholder screen as an operational workflow, and do not add secrets or
realistic private customer data to examples.
