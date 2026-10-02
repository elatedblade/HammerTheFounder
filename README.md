# Hammer The Founder (HTF)

> Managed job-search operations for candidates: HTF handles the search campaign, applications, and founder/CXO outreach while the candidate focuses on interviews.

## Product

Hammer The Founder (HTF) is a service platform for running managed job-search campaigns.

A client provides their profile, resume, target roles, compensation expectations, location preferences, and other constraints. HTF operators then execute the campaign manually in v1 and keep the client-facing dashboard up to date.

### Plans

- **Normal Apply** — managed job applications
- **Cold Apply** — managed founder/CXO outreach
- **Full-Throttle Sprint** — both workflows

The initial commercial flow is intentionally manual:

- Clients primarily communicate through WhatsApp.
- Payment is collected manually through HTF's QR/UPI flow.
- Applications are submitted manually by HTF operators.
- Cold outreach is manually sent by HTF operators in v1.
- Dashboard statuses are manually updated by HTF operators.
- AI assists research, matching, drafting, and QA but does not autonomously execute external actions in v1.

---

## Detailed implementation plan

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for the build plan, milestones, API/domain boundaries, database design, workflows, security model, testing strategy, and future automation seams.

---

## Engineering Principles

The system is designed as a **modular monolith** first, with explicit boundaries so individual components can be extracted later if scale requires it.

### Core principles

1. **Domain-first design** — business rules live in domain/application services, not views, serializers, or Celery tasks.
2. **Separation of concerns** — frontend, API, domain logic, infrastructure integrations, AI, and background jobs have clear boundaries.
3. **Single source of truth** — PostgreSQL stores campaign and workflow state. WhatsApp is an interface, not the system of record.
4. **Deterministic business rules** — AI proposes; application code validates and decides.
5. **Async by default for long-running work** — Celery handles AI processing, notifications, imports, and other background jobs.
6. **Idempotency** — every external/event-driven operation must be safe to retry.
7. **Auditability** — important state changes and operator actions are recorded.
8. **Least privilege** — operators, clients, admins, and service accounts get only the permissions they need.
9. **Provider abstraction** — WhatsApp, email, AI routing, storage, and auth integrations sit behind adapters/interfaces.
10. **Manual-first, automation-ready** — v1 optimizes the HTF operating workflow without coupling the domain model to browser automation.

---

# System Architecture

```text
                                      ┌──────────────────────┐
                                      │        CLIENT        │
                                      │  Next.js Web App     │
                                      │  WhatsApp            │
                                      └──────────┬───────────┘
                                                 │
                                                 ▼
                                      ┌──────────────────────┐
                                      │   Public/API Edge    │
                                      │       Django         │
                                      │   DRF + Auth Layer   │
                                      └──────────┬───────────┘
                                                 │
                         ┌───────────────────────┼────────────────────────┐
                         │                       │                        │
                         ▼                       ▼                        ▼
                 ┌──────────────┐       ┌──────────────┐        ┌──────────────┐
                 │ Candidate    │       │ Campaign     │        │ Billing      │
                 │ Domain       │       │ Domain       │        │ Domain       │
                 └──────┬───────┘       └──────┬───────┘        └──────────────┘
                        │                       │
                        └───────────────┬──────┘
                                        ▼
                               ┌────────────────┐
                               │  Application   │
                               │   & Outreach   │
                               │     Domains    │
                               └───────┬────────┘
                                       │
                              ┌────────▼─────────┐
                              │   PostgreSQL      │
                              │ System of Record │
                              └────────┬─────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
              ┌──────────┐      ┌────────────┐     ┌──────────────┐
              │  Celery  │      │ AI Gateway │     │ Object Store │
              │ + Redis  │      │  OmniRoute │     │    AWS S3    │
              └────┬─────┘      └─────┬──────┘     └──────────────┘
                   │                  │
                   ▼                  ▼
             Background Jobs     PydanticAI Agents

                         ┌──────────────────────────────┐
                         │      HTF ADMIN FRONTEND      │
                         │          Next.js             │
                         │ Ops / CRM / Task Queue       │
                         └──────────────────────────────┘

                         ┌──────────────────────────────┐
                         │        External Services     │
                         │ Google Auth / Resend /       │
                         │ WhatsApp (manual v1) / Sentry│
                         └──────────────────────────────┘
```

---

# Stack

| Area | Technology | Purpose |
|---|---|---|
| Client frontend | Next.js + TypeScript + Tailwind + shadcn/ui | Candidate onboarding and dashboard |
| Admin frontend | Next.js + TypeScript + Tailwind + shadcn/ui | Internal operations dashboard |
| Backend | Django + Django REST Framework | API, business logic, admin APIs, authentication integration |
| ORM | Django ORM | PostgreSQL persistence and query layer |
| Database | PostgreSQL | System of record |
| Async jobs | Celery | Background execution |
| Queue/broker | Redis | Celery broker/result backend and job coordination |
| File storage | AWS S3 | Resumes and user-uploaded documents |
| AI gateway | OmniRoute | Model routing/provider abstraction |
| AI framework | PydanticAI | Typed agent workflows and structured outputs |
| Transactional email | Resend | Product notifications and operational email |
| Auth | Clerk + Google OAuth | Managed identity; Google sign-in; Django verifies authenticated requests |
| WhatsApp | Manual WhatsApp Business workflow in v1 | Client communication; integration remains replaceable |
| Payments | Manual UPI/QR in v1 | Payment collection |
| Observability | Sentry | Errors, performance, frontend/backend monitoring |
| Containers | Docker / Docker Compose | Reproducible local development and deployment |
| Hosting | TBD | Keep deployment provider-agnostic initially |

## Auth decision

**Recommended v1: Clerk with Google OAuth.** Clerk supports Google as a social connection and provides frontend authentication components; the Django backend should verify the resulting authenticated token and map its external subject to the local Django `User` record. Keep provider-specific details isolated behind the authentication adapter so the rest of the application depends on a stable internal identity abstraction.

Do not let business logic depend directly on Clerk SDK objects. The boundary should be:

```text
Next.js + Clerk
      ↓
Bearer/session token
      ↓
Django authentication adapter
      ↓
local User
      ↓
roles + object permissions
```

For local development, Django should still own the application-level user record and authorization model even when authentication is delegated to the external identity provider.

---

# Repository Structure

Recommended monorepo:

```text
htf/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── Makefile
│
├── backend/
│   ├── manage.py
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── local.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   └── apps/
│       ├── users/
│       ├── candidates/
│       ├── resumes/
│       ├── campaigns/
│       ├── companies/
│       ├── jobs/
│       ├── applications/
│       ├── contacts/
│       ├── outreach/
│       ├── tasks/
│       ├── notifications/
│       ├── billing/
│       ├── audit/
│       ├── events/
│       ├── ai/
│       └── integrations/
│           ├── storage/
│           ├── email/
│           ├── whatsapp/
│           └── auth/
│
├── client-web/
│   ├── package.json
│   ├── Dockerfile
│   └── src/
│       ├── app/
│       ├── components/
│       ├── features/
│       ├── lib/
│       └── types/
│
├── admin-web/
│   ├── package.json
│   ├── Dockerfile
│   └── src/
│       ├── app/
│       ├── components/
│       ├── features/
│       ├── lib/
│       └── types/
│
└── infra/
    ├── docker/
    └── deployment/
```

---

# Domain Model

The initial domain model should be centered around **Candidate → Campaign → Work Items → Events**.

```text
User
 │
 └── CandidateProfile
       │
       ├── Resume(s)
       │
       └── Campaign(s)
             │
             ├── Applications ── Job ── Company
             │
             ├── Outreach ───── Contact ── Company
             │
             ├── HumanTasks
             │
             └── Events
```

## Core entities

### User

Application-level identity and authorization subject.

Important fields:

```text
id
identity_provider_subject
email
phone
role
is_active
created_at
updated_at
```

Roles should include at minimum:

```text
CLIENT
OPERATOR
ADMIN
```

### CandidateProfile

Canonical source of truth for candidate facts and preferences.

```text
user
full_name
headline
location
target_roles
target_industries
preferred_locations
remote_preference
expected_ctc_min
expected_ctc_max
experience_summary
work_authorization
sponsorship_requirement
notice_period
preferences_json
profile_version
```

The AI must read candidate facts from this model rather than creating its own unofficial copy.

### Resume

```text
id
candidate
s3_key
original_filename
content_type
file_size
parsed_text
parse_status
version
created_at
```

### Campaign

Represents one job-search engagement.

```text
id
candidate
plan
status
start_date
trial_end_date
billing_status
settings_json
version
created_at
updated_at
```

Campaign plans:

```text
NORMAL_APPLY
COLD_APPLY
FULL_THROTTLE
```

Campaign states:

```text
DRAFT
ONBOARDING
READY
ACTIVE
PAUSED
COMPLETED
CANCELLED
```

### Company

Canonical company record used by both job applications and outreach.

### Job

Normalized opportunity record.

```text
id
company
external_source
external_id
canonical_url
title
location
employment_type
description
status
first_seen_at
last_seen_at
fingerprint
metadata_json
```

The `fingerprint` supports duplicate detection across sources.

### Application

Represents a candidate's application to a specific job.

Recommended status enum:

```text
DISCOVERED
SHORTLISTED
QUEUED
IN_PROGRESS
SUBMITTED
APPLICATION_FAILED
IN_REVIEW
RECRUITER_CONTACTED
INTERVIEW
INTERVIEW_SCHEDULED
REJECTED
OFFER
WITHDRAWN
```

### Contact

Potential outreach recipient associated with a company.

### Outreach

```text
id
campaign
contact
channel
status
subject
body
sent_at
thread_reference
last_response_at
follow_up_due_at
```

### HumanTask

Internal work queue for exceptions and operational work.

```text
id
campaign
entity_type
entity_id
task_type
priority
status
assigned_to
payload_json
created_at
completed_at
```

Task types:

```text
PROFILE_REVIEW
APPLICATION_REVIEW
UNKNOWN_APPLICATION_QUESTION
CONTACT_REVIEW
OUTREACH_REVIEW
BOUNCE_REVIEW
INTERVIEW_REVIEW
OTHER
```

### Event

Immutable domain/audit event.

```text
id
aggregate_type
aggregate_id
event_type
actor_type
actor_id
payload_json
created_at
```

Examples:

```text
CAMPAIGN_CREATED
CAMPAIGN_STARTED
APPLICATION_CREATED
APPLICATION_SUBMITTED
APPLICATION_STATUS_CHANGED
OUTREACH_CREATED
OUTREACH_SENT
OUTREACH_REPLIED
INTERVIEW_DETECTED
INTERVIEW_SCHEDULED
HUMAN_TASK_CREATED
HUMAN_TASK_COMPLETED
PAYMENT_MARKED_RECEIVED
```

---

# Layered Backend Architecture

Each Django app should follow a predictable internal structure.

```text
apps/campaigns/
├── models.py
├── selectors.py
├── services.py
├── policies.py
├── serializers.py
├── views.py
├── urls.py
├── tasks.py
├── admin.py
└── tests/
```

### Responsibilities

**Models**

Persistence and database constraints.

**Selectors**

Read-only query logic.

**Services**

Business use cases and state transitions.

**Policies**

Authorization and domain rules.

**Serializers**

API input/output validation.

**Views**

HTTP transport only. Views should delegate business logic to services.

**Tasks**

Celery wrappers that invoke application services. Tasks should remain thin and retry-safe.

---

# Request Flow

Typical client dashboard request:

```text
Next.js
  │
  │ HTTPS
  ▼
Django REST API
  │
  ▼
Auth / Permission
  │
  ▼
Application Service
  │
  ▼
Selector / ORM
  │
  ▼
PostgreSQL
  │
  ▼
DTO / Serializer
  │
  ▼
Next.js
```

Do not allow the frontend to make assumptions about database state. The API owns business truth.

---

# Campaign Lifecycle

```text
               ┌───────────────┐
               │     DRAFT     │
               └───────┬───────┘
                       │ onboarding complete
                       ▼
               ┌───────────────┐
               │     READY     │
               └───────┬───────┘
                       │ operator starts
                       ▼
               ┌───────────────┐
               │     ACTIVE    │◄──────────────┐
               └───────┬───────┘               │
                       │                       │ resume
             ┌─────────┴────────┐              │
             ▼                  ▼              │
          PAUSED            COMPLETED          │
             │                                │
             └────────────────────────────────┘
```

A campaign has a plan configuration that controls which work queues are available:

```text
NORMAL_APPLY  -> application workflow
COLD_APPLY    -> outreach workflow
FULL_THROTTLE -> both
```

---

# Manual Operations Workflow (v1)

The v1 objective is to make HTF operators extremely efficient.

## Application workflow

```text
Job discovered
      ↓
Operator reviews job
      ↓
Match against CandidateProfile
      ↓
Create Application
      ↓
Operator submits manually
      ↓
Record result
      ↓
Emit event
      ↓
Dashboard updated
      ↓
Client notification if relevant
```

## Outreach workflow

```text
Target company discovered
      ↓
Contact selected
      ↓
AI can draft/personalize message
      ↓
Operator reviews
      ↓
Operator sends manually
      ↓
Record Outreach
      ↓
Emit event
      ↓
Dashboard updated
```

This architecture deliberately avoids browser automation and automated external submissions in v1.

---

# AI Architecture

The AI layer should be treated as an application subsystem, not as the business layer itself.

```text
Django Application Service
          │
          ▼
       AI Service
          │
          ▼
     PydanticAI Agent
          │
          ▼
       OmniRoute
          │
     ┌────┼────┐
     ▼    ▼    ▼
   LLM-A LLM-B LLM-C
```

## Initial agents

### Profile Agent

Extracts structured candidate facts from resumes/intake responses.

### Job Matching Agent

Produces typed matching results.

Example output:

```python
class JobMatchResult(BaseModel):
    job_id: UUID
    score: float
    matched_skills: list[str]
    concerns: list[str]
    recommendation: Literal["SHORTLIST", "REJECT", "REVIEW"]
```

### Outreach Personalization Agent

Creates a concise, factually grounded outreach draft from approved candidate and company data.

### QA Agent

Checks generated content for unsupported claims, missing information, duplication, or policy violations before an operator sees it as ready.

### Notification Agent

Optional later component for deciding which events merit a client notification.

## AI rule

**AI proposes; deterministic code decides.**

For example:

```python
result = match_job(candidate, job)

if (
    result.recommendation == "SHORTLIST"
    and result.score >= MIN_MATCH_SCORE
    and not application_exists(candidate, job)
):
    create_application_queue_item(candidate, job)
```

Do not give an LLM unrestricted ability to mutate production state.

---

# Celery / Redis Architecture

Redis is used for job brokering and coordination, not as the primary database.

```text
Django request
     │
     ▼
create task
     │
     ▼
Redis broker
     │
     ▼
Celery worker
     │
     ├── AI processing
     ├── resume parsing
     ├── notifications
     ├── scheduled follow-ups
     └── analytics jobs
```

Tasks must be idempotent.

Example:

```python
@app.task(bind=True, autoretry_for=(TemporaryError,), max_retries=3)
def process_resume(resume_id):
    ...
```

Before processing, verify whether the work has already completed.

Use a database record or idempotency key rather than assuming Celery will execute a task exactly once.

---

# API Design

Use versioned REST APIs.

```text
/api/v1/auth/
/api/v1/candidates/
/api/v1/resumes/
/api/v1/campaigns/
/api/v1/jobs/
/api/v1/applications/
/api/v1/companies/
/api/v1/contacts/
/api/v1/outreach/
/api/v1/tasks/
/api/v1/dashboard/
/api/v1/notifications/
/api/v1/billing/
/api/v1/admin/
```

Example endpoints:

```text
GET    /api/v1/candidate/profile
PATCH  /api/v1/candidate/profile
POST   /api/v1/candidate/resumes

GET    /api/v1/campaigns
POST   /api/v1/campaigns
GET    /api/v1/campaigns/{id}
POST   /api/v1/campaigns/{id}/start
POST   /api/v1/campaigns/{id}/pause
POST   /api/v1/campaigns/{id}/resume

GET    /api/v1/campaigns/{id}/applications
GET    /api/v1/campaigns/{id}/outreach
GET    /api/v1/campaigns/{id}/events
GET    /api/v1/campaigns/{id}/metrics

GET    /api/v1/admin/tasks
POST   /api/v1/admin/tasks/{id}/claim
POST   /api/v1/admin/tasks/{id}/complete
```

Avoid endpoint-specific business logic such as updating five tables manually inside a view. Use domain/application services.

---

# Dashboard Metrics

The client dashboard should focus on campaign activity and progression.

Application metrics:

```text
Applications submitted
Applications in review
Interviews
Offers
Rejections
```

Outreach metrics:

```text
Messages sent
Replies
Positive replies
Interviews
Bounces
```

Every metric must have a clearly defined query and denominator. Do not create ambiguous counters such as `accepted` without a documented meaning.

---

# Admin Dashboard

The admin frontend is a first-class product surface for HTF operators.

## Main screens

### Clients

```text
Client
Plan
Campaign status
Application volume
Outreach volume
Latest activity
Issues
```

### Campaign workspace

```text
Candidate profile
Campaign settings
Applications
Outreach
Human tasks
Timeline
Internal notes
```

### Task queue

```text
Priority
Task type
Candidate
Age
Assignee
Status
```

### Activity timeline

A chronological view of all important campaign events.

---

# Authentication & Authorization

Authentication is delegated to the managed identity provider.

Authorization remains an HTF responsibility.

```text
Identity Provider
      │
      ▼
Authenticated principal
      │
      ▼
Django User
      │
      ▼
Role + object-level authorization
```

Clients must only access objects belonging to their own account.

Operators can access assigned/authorized campaigns.

Admins can access the full operational dataset.

Do not trust a client-provided `candidate_id` or `campaign_id` without verifying ownership/permission server-side.

---

# Storage

AWS S3 stores uploaded files.

Recommended pattern:

```text
Browser
  │
  │ signed upload request
  ▼
Django
  │
  │ presigned URL
  ▼
S3
```

The frontend should not send large files through Django unless there is a specific reason to do so.

Store S3 object keys in PostgreSQL, not full public URLs.

Example:

```text
s3://bucket/candidates/{candidate_id}/resumes/{resume_id}/original.pdf
```

Keep the bucket private and issue short-lived signed download URLs where appropriate.

---

# Notifications

Create a notification abstraction now even though WhatsApp is manual in v1.

```text
NotificationService
      │
      ├── WhatsAppAdapter
      ├── EmailAdapter
      └── InAppAdapter
```

In v1, the operator may perform WhatsApp communication manually while the platform stores notification records and templates.

Later, an official WhatsApp integration can replace the adapter without changing campaign/business logic.

---

# Email

Resend is used for transactional email in v1.

Examples:

```text
Welcome / onboarding
Campaign started
Payment reminder
Important campaign event
Interview notification
Password/authentication events if applicable
```

Do not mix transactional email infrastructure with future cold-outreach sending infrastructure.

---

# Payment Model (v1)

Payment is intentionally manual.

```text
Client
  ↓
WhatsApp
  ↓
HTF QR / UPI
  ↓
Operator verifies payment
  ↓
Payment record created
  ↓
Campaign billing state updated
```

The backend should still maintain payment records so a real payment provider can be introduced later without changing the campaign model.

Example payment states:

```text
PENDING
MARKED_RECEIVED
FAILED
REFUNDED
```

---

# Event & Audit Architecture

Important mutations should produce events.

Example:

```text
Operator submits application
        │
        ▼
ApplicationService.submit()
        │
        ├── database transaction
        │       ├── Application.status = SUBMITTED
        │       └── Event(APPLICATION_SUBMITTED)
        │
        └── enqueue notification task after commit
```

Prefer transaction-safe task publication using a pattern such as Django's `transaction.on_commit()` so Celery does not process stale/uncommitted database state.

Audit logs should capture:

```text
actor
action
entity
entity_id
before/after where appropriate
request metadata where appropriate
timestamp
```

---

# Reliability & Failure Handling

## External dependency failure

Never let a failed email/API/AI provider call corrupt campaign state.

Use:

```text
timeout
retry with backoff
idempotency
circuit breaking where appropriate
failure status
human task for unresolved failures
```

## Celery retry

A retried task must not:

- submit the same logical action twice
- create duplicate outreach records
- send duplicate notifications
- overwrite newer state

## Database transactions

Use Django transactions around multi-step domain mutations.

Example:

```python
with transaction.atomic():
    application.mark_submitted()
    Event.objects.create(...)
```

---

# Security Baseline

HTF handles sensitive candidate data, therefore security is a product requirement.

Minimum v1 controls:

- HTTPS everywhere outside local development
- private S3 bucket
- signed URLs for private files
- secrets stored in environment/secret-management systems, never git
- strong role-based authorization
- object-level access checks
- secure session/token handling
- database backups
- audit logs for privileged actions
- Sentry configured without leaking secrets or sensitive payloads
- input validation at API boundaries
- upload MIME/type/size validation
- malware scanning for uploaded documents when operationally justified
- dependency scanning and regular upgrades

Do not store third-party passwords for clients.

---

# Frontend Architecture

Both frontends use the same design philosophy:

```text
src/
├── app/
├── components/
├── features/
│   ├── auth/
│   ├── campaigns/
│   ├── applications/
│   ├── outreach/
│   ├── dashboard/
│   └── profile/
├── lib/
│   ├── api/
│   ├── auth/
│   └── utils/
└── types/
```

Feature components should own feature-specific UI and state. Shared UI components live in `components/`.

The API client should be centralized rather than scattering `fetch()` calls throughout the application.

---

# Observability

Sentry is the initial observability platform.

Instrument:

### Backend

- request failures
- Celery task failures
- AI failures
- external integration failures
- database errors
- important performance spans

### Frontend

- runtime errors
- API failures
- key user-flow failures

Do not send raw resumes, complete private emails, auth tokens, or other unnecessary PII into Sentry.

Later, add distributed tracing/OpenTelemetry if service boundaries or workload size justify it.

---

# Testing Strategy

Testing should follow the architecture boundary.

## Unit tests

Test domain rules and services:

```text
CampaignService
ApplicationService
OutreachService
BillingService
Permission policies
Matching policies
```

## Integration tests

Test:

```text
Django + PostgreSQL
Django + Redis/Celery
S3 integration
Auth integration
Resend integration
```

## API tests

Test request/response contracts and permissions.

## Frontend tests

Test important user journeys:

```text
sign in
complete onboarding
start campaign
view dashboard
view application
view outreach
```

## End-to-end tests

Initially keep E2E coverage focused on the most valuable flows rather than attempting to cover every admin table.

---

# Implementation Roadmap

## Phase 0 — Repository & Infrastructure

Goal: reproducible local development.

Tasks:

1. Create monorepo.
2. Add Docker Compose.
3. Add Django backend.
4. Add PostgreSQL.
5. Add Redis.
6. Add Celery worker.
7. Add client Next.js app.
8. Add admin Next.js app.
9. Add `.env.example`.
10. Add linting/formatting/test tooling.
11. Add basic Sentry integration.

Definition of done:

```text
docker compose up
```

starts the local development environment.

---

## Phase 1 — Identity & Roles

Goal: a secure multi-role foundation.

Tasks:

1. Configure managed Google authentication.
2. Create Django User model.
3. Map external identity → internal user.
4. Create CLIENT / OPERATOR / ADMIN roles.
5. Implement API permission classes/policies.
6. Add client/admin route protection.

Definition of done:

A client cannot access another client's campaign.

---

## Phase 2 — Candidate Onboarding

Goal: collect everything HTF needs to run a campaign.

Tasks:

1. CandidateProfile model.
2. Resume model.
3. S3 upload flow.
4. Intake form.
5. Profile completion status.
6. Resume parsing job.
7. Profile review UI.
8. Operator profile verification.

Flow:

```text
Sign in
  ↓
Intake form
  ↓
Resume upload
  ↓
Profile extraction
  ↓
Operator review
  ↓
Candidate approved
```

---

## Phase 3 — Campaigns

Goal: turn a profile into a managed engagement.

Tasks:

1. Campaign model.
2. Plan enum.
3. Campaign settings.
4. Start/pause/resume lifecycle.
5. Trial period fields.
6. Campaign versioning.
7. Campaign activity timeline.

Definition of done:

An operator can create a campaign, configure it, activate it, pause it, and resume it.

---

## Phase 4 — Applications

Goal: manually manage applications end-to-end.

Tasks:

1. Company model.
2. Job model.
3. Application model.
4. Duplicate job fingerprinting.
5. Application status state machine.
6. Operator application workspace.
7. Candidate application table.
8. Timeline/events.
9. Application metrics.
10. Failure/review tasks.

Initial operator workflow:

```text
Find job
 ↓
Create/select Job
 ↓
Check duplicate
 ↓
Check candidate fit
 ↓
Submit manually
 ↓
Set status
 ↓
Record notes/evidence
```

---

## Phase 5 — Outreach

Goal: manually execute cold outreach while making it measurable.

Tasks:

1. Contact model.
2. Outreach model.
3. Contact deduplication.
4. Suppression list.
5. Outreach status machine.
6. Message templates.
7. Operator outreach workspace.
8. Reply tracking.
9. Follow-up scheduling fields.

Do not implement automated mass outreach in this phase.

---

## Phase 6 — Client Dashboard

Goal: make HTF's work visible and trustworthy.

Dashboard sections:

```text
Overview
Applications
Outreach
Interviews
Activity
Profile
Campaign
```

Show counts derived from backend queries, not frontend-maintained counters.

---

## Phase 7 — WhatsApp & Notifications

Goal: make WhatsApp the primary customer communication channel without making it the system of record.

Phase 7a:

- operator sends WhatsApp manually
- backend stores notification records
- standardized templates

Phase 7b:

- integrate an official provider
- webhook ingestion
- delivery tracking
- inbound message routing

Keep the provider behind an adapter.

---

## Phase 8 — Billing

Goal: preserve manual collection but model it properly.

Tasks:

1. Payment model.
2. Manual payment verification.
3. Payment state machine.
4. Campaign billing status.
5. Trial expiration logic.
6. Admin payment screen.
7. Client payment state.

Later:

```text
Manual payment
     ↓
Payment adapter
     ↓
Razorpay/Stripe/etc.
```

---

## Phase 9 — AI Foundation

Only after the human workflow works should AI be deeply integrated.

Tasks:

1. Create AI service abstraction.
2. Integrate OmniRoute.
3. Integrate PydanticAI.
4. Define structured output schemas.
5. Add prompt versioning.
6. Add model/latency/cost logging.
7. Add Profile Agent.
8. Add Job Match Agent.
9. Add Outreach Personalization Agent.
10. Add QA Agent.

Every agent should have:

```text
input schema
output schema
tool permissions
retry policy
max execution budget
prompt version
```

---

## Phase 10 — Workflow Intelligence

After enough real HTF campaigns exist:

```text
Applications
   ↓
Interview data
   ↓
Offer data
   ↓
Campaign analytics
   ↓
Optimization recommendations
```

Potential intelligence features:

- role fit analysis
- company targeting
- outreach personalization quality
- campaign health
- conversion funnel analysis
- operator productivity
- AI cost analysis

---

# Future Automation Boundary

The manual v1 should be designed so future automation can replace operator actions without changing the domain model.

Current:

```text
ApplicationService
       ↓
Operator executes externally
       ↓
Operator records result
```

Future:

```text
ApplicationService
       ↓
Execution Gateway
   ┌───┴────────┐
   ▼            ▼
Human       Approved Integration
```

Likewise for outreach:

```text
OutreachService
       ↓
Execution Gateway
   ┌───┴────────┐
   ▼            ▼
Human       Authorized Provider
```

The domain should never know whether an action was completed by a human or an approved external integration.

---

# State Machine Rules

State transitions should be explicit and validated.

Example application transition map:

```text
DISCOVERED → SHORTLISTED
SHORTLISTED → QUEUED
QUEUED → IN_PROGRESS
IN_PROGRESS → SUBMITTED
IN_PROGRESS → APPLICATION_FAILED
SUBMITTED → IN_REVIEW
IN_REVIEW → RECRUITER_CONTACTED
RECRUITER_CONTACTED → INTERVIEW
INTERVIEW → INTERVIEW_SCHEDULED
INTERVIEW_SCHEDULED → OFFER
INTERVIEW_SCHEDULED → REJECTED
```

Do not allow arbitrary status changes from the UI.

The service layer owns transitions.

---

# Data Integrity Rules

Critical database constraints should include:

- unique user identity mapping
- unique campaign identifiers
- unique external job identifiers per source
- duplicate application prevention for a candidate/job pair
- unique contact identifiers where appropriate
- unique idempotency keys for external actions
- foreign keys for all core relations
- timestamps on all mutable business objects

Use PostgreSQL indexes for the high-frequency paths:

```text
candidate_id
campaign_id
status
created_at
company_id
external_source + external_id
```

Measure query performance before adding broad indexes.

---

# Coding Standards

Backend:

- Python 3.x
- Django
- Django REST Framework
- type hints
- service/selectors/policy separation
- small Celery tasks
- explicit transactions
- migrations committed to git

Frontend:

- TypeScript
- ESLint
- consistent API client
- typed DTOs
- reusable components
- server/client boundaries kept intentional

Git:

```text
main       → production
 develop   → integration
 feature/* → development
```

Prefer small pull requests with one architectural concern per change.

---

# Environment Variables

At minimum:

```text
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=
DATABASE_URL=
REDIS_URL=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_REGION=
RESEND_API_KEY=
SENTRY_DSN=
OMNIROUTE_BASE_URL=
OMNIROUTE_API_KEY=
AUTH_ISSUER_URL=
AUTH_CLIENT_ID=
AUTH_CLIENT_SECRET=
```

Never commit actual secrets.

---

# Local Development

Recommended services:

```text
client-web
admin-web
backend
worker
postgres
redis
```

Expected development command:

```bash
docker compose up --build
```

Then run Django migrations and create the first admin user.

---

# Definition of Done for v1

HTF v1 is ready for controlled real-world use when a complete client journey works:

```text
Client signs in
   ↓
Completes intake
   ↓
Uploads resume
   ↓
HTF verifies profile
   ↓
HTF creates campaign
   ↓
Client sees campaign
   ↓
Operator records applications
   ↓
Operator records outreach
   ↓
Events update timeline
   ↓
Dashboard shows accurate metrics
   ↓
Operator communicates via WhatsApp
   ↓
Payment is recorded manually
```

The system should be able to explain the status of every application and outreach item without relying on operator memory.

---

# Non-Goals for v1

Do **not** build these initially:

- autonomous browser-based job application bots
- automated LinkedIn scraping
- automated mass cold-email blasting
- complex microservices
- real-time distributed event streaming
- sophisticated recommendation models
- automated payment reconciliation
- automated WhatsApp agent conversations
- dozens of AI agents communicating freely with one another

First prove the business workflow.

---

# Future Extraction Candidates

Keep these as logical modules in the monolith today. Extract them only if actual scale or operational isolation requires it.

```text
Potential future services:

AI Gateway / AI Workers
Notification Service
Search / Job Ingestion Service
Analytics Service
Billing Service
```

Do not create these as networked microservices before there is a concrete need.

---

# Architecture Decision Records

Create ADRs under `docs/adr/` for decisions that materially affect the system.

Suggested initial ADRs:

```text
0001-modular-monolith.md
0002-postgresql.md
0003-celery-redis.md
0004-managed-auth.md
0005-omniroute-ai-gateway.md
0006-manual-operations-v1.md
0007-s3-private-storage.md
```

Each ADR should capture:

```text
Context
Decision
Alternatives considered
Consequences
```

---

# Immediate Build Order

The recommended implementation sequence is:

```text
1. Monorepo + Docker
2. Django + PostgreSQL + Redis + Celery
3. User/auth/roles
4. Candidate profile + resume/S3
5. Campaigns
6. Companies + jobs
7. Applications + state machine
8. Human task queue
9. Outreach + contacts
10. Client dashboard
11. Admin dashboard
12. Events + audit trail
13. Resend notifications
14. Manual billing records
15. OmniRoute + PydanticAI
16. AI-assisted matching/drafting/QA
17. Official WhatsApp integration when operationally justified
18. Future approved execution automation
```

The order is deliberate: **build the source of truth and operator workflow before automating the execution.**
