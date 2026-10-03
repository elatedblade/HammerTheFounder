# HTF Implementation Plan — new by harshit

## Harshit's revised product direction (2026-10-03)

This is a copy, not a replacement of `IMPLEMENTATION_PLAN.md`. This revision
takes precedence over the retained reference below for the customer journey.

### Exactly three primary customer pages

1. **Landing `/`:** public marketing explaining HTF, its target customers, managed
   applications and founder/CXO outreach, three service plans, process and FAQs.
   Clear plan-selection/WhatsApp CTA and sign-in/account controls. No invented
   prices, testimonials, logos, urgency or guaranteed hiring outcomes.
2. **Profile `/profile`:** authenticated intake, preferences, compensation, work
   authorization, resume upload/download and review state. No full intake form on
   the dashboard.
3. **Dashboard `/dashboard`:** selected inquiry/plan, campaign status, next action,
   truthful metrics and compact application/outreach/interview/activity/payment/
   communication sections. No internal notes, operational controls, raw IDs or AI
   configuration. `/workspace` redirects here; Clerk auth routes are supporting
   routes, not additional product pages.

### Plan selection and WhatsApp journey

Landing → select plan → sign in/create account if needed → save owned inquiry →
explicitly open configured business WhatsApp with plan and inquiry reference →
discuss with HTF → intake/review → admin converts inquiry to campaign → admin
starts campaign. Link opening is not proof a message was sent, payment was made,
or campaign activated. Persist inquiries and expose them in admin; retries must
not duplicate inquiries/campaigns. Do not require a completed profile just to
inquire. Preserve normal review/readiness rules for campaign activation.

The owner supplies the business WhatsApp number. Missing configuration is an
honest setup state, never a made-up destination or personal account phone.

### Marketing and maintainability

Position HTF as a human-operated managed job-search service, not an autonomous
job bot or guarantee of employment. Explain actual deliverables and fit. Build a
cohesive responsive design with accessible navigation and focused conversion.
Keep marketing copy, design tokens and presentation separate from stable plan
identifiers, API contracts, permissions and workflows. Redesigns must not alter
authentication, inquiry persistence, billing or campaign state.

### EC2 without a purchased domain

Prepare a single-EC2 evaluation deployment, without launching AWS resources or
promising it is free. Account eligibility/credits, instance architecture, public
IPv4, EBS, snapshots and egress all affect cost. Prefer building images elsewhere
rather than building two Next apps alongside PostgreSQL/Celery on a tiny instance.
Use HTTPS with a supported hostname or an SSH-tunneled localhost evaluation.
Do not expose real candidate PII or passwords over public HTTP. Verify Clerk's
requirements before claiming production auth works on a bare IP. Keep database,
Redis and internal API ports private; document secrets, migrations, backups,
recovery and later domain/TLS cutover.

### Acceptance criteria

- Landing is public, complete, clear about service scope and honest about outcomes.
- Selected plan survives sign-in; an explicit action saves inquiry and opens the
  configured WhatsApp. No automatic external communication or duplicate conversion.
- Admin can find the inquiry, create the correctly linked campaign, review and
  activate it under existing permissions.
- Profile/resume work is separate from the progress-focused dashboard.
- Styling/copy changes are isolated from business logic.
- Combined checks cover inquiry ownership/conversion, routing, frontend build and
  permissions. Live provider/deployment blockers remain explicit.

---

# Original architecture and implementation reference

> Implementation update (2026-10-03): core manual-first domain APIs and both
> workspaces are now implemented, including billing, communications, task/event
> workflows and bounded AI proposals. See `DELIVERY_STATUS.md` for verified checks
> and remaining launch requirements. This document remains the design/acceptance
> reference; a described future capability is not automatically a completed feature.

## 1. Objective

Build a production-capable MVP for Hammer The Founder (HTF) that lets HTF operate managed job-search campaigns for clients.

The MVP deliberately keeps **external execution manual**:

- HTF operators manually submit job applications.
- HTF operators manually send cold outreach.
- HTF operators manually update application/outreach statuses.
- HTF operators communicate with customers primarily over WhatsApp.
- Payments are verified manually through UPI/QR.

The software's job in v1 is to become the **system of record and operating system for HTF**.

---

# 2. Architecture Decision

## Architectural style

Use a **modular monolith**.

```text
                         Django Monolith
┌────────────────────────────────────────────────────────────┐
│                                                            │
│ Users   Candidates   Campaigns   Jobs   Applications       │
│ Outreach   Tasks   Notifications   Billing   Audit   AI    │
│                                                            │
└────────────────────────────┬───────────────────────────────┘
                             │
                       PostgreSQL
```

Each module has clear ownership of its data and business rules.

No microservices in v1.

## Why

The major complexity initially is business workflow, not infrastructure scale. A monolith gives us:

- transactional consistency across domains
- easy local development
- simple deployments
- fewer network failure modes
- easier debugging
- easier refactoring while requirements are still moving

Later, components can be extracted based on measured bottlenecks.

---

# 3. Stack Matrix

| Concern             | Decision                                                 |
| ------------------- | -------------------------------------------------------- |
| Client frontend     | Next.js + TypeScript + Tailwind CSS + shadcn/ui          |
| Admin frontend      | Separate Next.js + TypeScript + Tailwind CSS + shadcn/ui |
| Backend             | Django + Django REST Framework                           |
| ORM                 | Django ORM                                               |
| Database            | PostgreSQL                                               |
| Background jobs     | Celery                                                   |
| Broker              | Redis                                                    |
| Object storage      | AWS S3                                                   |
| Auth                | Clerk + Google OAuth                                     |
| Transactional email | Resend free tier initially                               |
| WhatsApp v1         | Manual WhatsApp Business App                             |
| Payments v1         | Manual UPI/QR + admin verification                       |
| AI gateway          | OmniRoute                                                |
| Agent framework     | PydanticAI                                               |
| Observability       | Sentry                                                   |
| Packaging/runtime   | Docker                                                   |
| Hosting             | Provider-neutral initially                               |

The WhatsApp Business app is free to download and intended for small-business customer communication; HTF will use the app manually in v1 rather than integrating the WhatsApp Business Platform immediately. citeturn105091search0turn105091search1

Clerk supports Google as an OAuth/social connection, and its current free plan includes a large user allowance; the current documented limit is 50,000 monthly retained users. citeturn747893search0turn747893search1turn689300search7

---

# 4. High-Level System

```text
                                 ┌──────────────────────┐
                                 │        CLIENT        │
                                 │                      │
                                 │ Next.js              │
                                 │ WhatsApp             │
                                 └──────────┬───────────┘
                                            │ HTTPS
                                            ▼
                                 ┌──────────────────────┐
                                 │       DJANGO         │
                                 │      REST API        │
                                 └──────────┬───────────┘
                                            │
                 ┌──────────────────────────┼─────────────────────────┐
                 │                          │                         │
                 ▼                          ▼                         ▼
          Candidate Domain           Campaign Domain           Billing Domain
                 │                          │                         │
                 └──────────────────────────┼─────────────────────────┘
                                            │
                                            ▼
                                   PostgreSQL System of Record
                                            │
           ┌────────────────────────────────┼────────────────────────┐
           │                                │                        │
           ▼                                ▼                        ▼
      Redis Broker                     AWS S3                  External APIs
           │                                                     │
           ▼                              ┌──────────────────────┼───────────┐
     Celery Workers                       │                      │           │
           │                             Resend                Clerk       Sentry
           ▼
      AI Service
           │
           ▼
       PydanticAI
           │
           ▼
       OmniRoute
           │
           ▼
        LLMs

                    ┌─────────────────────────────────┐
                    │         ADMIN FRONTEND          │
                    │         Separate Next.js        │
                    │ Clients / Campaigns / Tasks    │
                    │ Applications / Outreach / Ops   │
                    └─────────────────────────────────┘
```

---

# 5. Responsibility Boundaries

## Next.js client application

Owns:

- rendering
- client navigation
- forms
- dashboard presentation
- API calls
- frontend authentication UI

Does not own:

- business truth
- campaign transitions
- permissions
- billing status
- application counters

## Next.js admin application

Owns:

- internal operations interface
- operator work queues
- client management
- campaign management
- application and outreach updates
- internal notes
- payment verification

Does not directly mutate PostgreSQL.

## Django

Owns:

- domain logic
- authorization
- API contracts
- database transactions
- campaign state
- application state
- event creation
- integration orchestration

## Celery

Owns:

- asynchronous jobs
- retries
- scheduled work
- AI processing
- notifications
- document processing

Celery tasks should be thin wrappers around application services.

## PostgreSQL

Single source of truth for business state.

Redis is not a substitute for PostgreSQL.

---

# 6. Backend Module Structure

```text
backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   ├── celery.py
│   ├── asgi.py
│   └── wsgi.py
│
└── apps/
    ├── users/
    ├── candidates/
    ├── resumes/
    ├── campaigns/
    ├── companies/
    ├── jobs/
    ├── applications/
    ├── contacts/
    ├── outreach/
    ├── tasks/
    ├── notifications/
    ├── billing/
    ├── events/
    ├── audit/
    ├── ai/
    └── integrations/
        ├── auth/
        ├── storage/
        ├── email/
        └── whatsapp/
```

A domain app should normally look like:

```text
campaigns/
├── models.py
├── services.py
├── selectors.py
├── policies.py
├── serializers.py
├── views.py
├── urls.py
├── tasks.py
├── admin.py
└── tests/
```

### Layer rules

`views.py`

HTTP transport only.

`serializers.py`

API input/output validation.

`services.py`

Business use cases and state transitions.

`selectors.py`

Read/query logic.

`policies.py`

Authorization and rules.

`tasks.py`

Celery entrypoints only.

`models.py`

Persistence representation and database constraints.

---

# 7. Core Data Model

```text
User
 │
 └── CandidateProfile
       │
       ├── Resume
       │
       └── Campaign
             │
             ├── Application ── Job ── Company
             │
             ├── Outreach ───── Contact ── Company
             │
             ├── HumanTask
             │
             └── Event
```

## User

Application-level identity.

Fields:

```text
id
identity_provider
identity_provider_subject
email
phone
role
is_active
created_at
updated_at
```

Roles:

```text
CLIENT
OPERATOR
ADMIN
```

## CandidateProfile

Canonical candidate facts.

```text
id
user_id
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
created_at
updated_at
```

Use a structured representation for frequently queried fields and JSON for flexible/non-critical preferences.

## Resume

```text
id
candidate_id
s3_key
original_filename
content_type
file_size
parsed_text
parse_status
version
created_at
```

## Campaign

```text
id
candidate_id
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

Plans:

```text
NORMAL_APPLY
COLD_APPLY
FULL_THROTTLE
```

Statuses:

```text
DRAFT
ONBOARDING
READY
ACTIVE
PAUSED
COMPLETED
CANCELLED
```

## Company

Canonical organization record shared by jobs and outreach.

## Job

```text
id
company_id
external_source
external_id
canonical_url
title
location
employment_type
description
status
fingerprint
first_seen_at
last_seen_at
metadata_json
```

The `fingerprint` supports cross-source duplicate detection.

## Application

```text
id
campaign_id
job_id
status
submitted_at
notes
operator_id
source_reference
created_at
updated_at
```

Candidate/job duplicate protection should be enforced in the database and application service.

## Contact

```text
id
company_id
name
title
email
profile_url
source
metadata_json
```

## Outreach

```text
id
campaign_id
contact_id
channel
status
subject
body
sent_at
reply_at
follow_up_due_at
thread_reference
operator_id
created_at
updated_at
```

## HumanTask

```text
id
campaign_id
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

## Event

Immutable record of important business events.

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

## AuditLog

Used for privileged/operator changes where an explicit audit trail is required.

---

# 8. State Machines

State changes must go through domain services.

## Application

```text
DISCOVERED
    ↓
SHORTLISTED
    ↓
QUEUED
    ↓
IN_PROGRESS
    ├─────────────→ APPLICATION_FAILED
    ↓
SUBMITTED
    ↓
IN_REVIEW
    ↓
RECRUITER_CONTACTED
    ↓
INTERVIEW
    ↓
INTERVIEW_SCHEDULED
    ├─────────────→ REJECTED
    ↓
OFFER
```

## Outreach

```text
TARGET_IDENTIFIED
       ↓
CONTACT_VERIFIED
       ↓
DRAFTED
       ↓
REVIEW_REQUIRED
       ↓
SENT
   ┌───┼───────────┐
   ▼   ▼           ▼
DELIVERED BOUNCED  REPLIED
                   │
             ┌─────┴─────┐
             ▼           ▼
       POSITIVE_REPLY NEGATIVE_REPLY
```

The UI should not expose arbitrary status mutation. It should call transition endpoints/services.

---

# 9. Application Workflow — v1 Manual

```text
Operator finds job
        ↓
Select/create Company
        ↓
Create normalized Job
        ↓
Check duplicate application
        ↓
Review candidate fit
        ↓
Create Application
        ↓
Submit externally manually
        ↓
Record outcome
        ↓
ApplicationService transition
        ↓
Event created
        ↓
Dashboard reflects state
        ↓
Notification queued if required
```

Important properties:

- no automated browser execution in v1
- no candidate credentials stored
- duplicate applications blocked
- all operator actions auditable

---

# 10. Outreach Workflow — v1 Manual

```text
Operator identifies company
        ↓
Selects contact
        ↓
Checks duplicate/suppression
        ↓
AI optionally drafts message
        ↓
Operator reviews
        ↓
Operator sends manually
        ↓
Record Outreach
        ↓
Event created
        ↓
Dashboard updates
```

Automated mass cold-email execution is intentionally outside v1.

---

# 11. Human Task Queue

This should be one of the first operational features.

```text
                    TASK QUEUE

HIGH
────────────────────────────────
Unknown application question     Candidate A
Interview confirmation           Candidate B

MEDIUM
────────────────────────────────
Contact verification             Candidate C
Outreach review                  Candidate D

LOW
────────────────────────────────
Profile cleanup                  Candidate E
```

Operators work from tasks rather than browsing the whole database manually.

Every task has:

```text
priority
assignee
status
created_at
age
entity reference
```

---

# 12. Client Dashboard

## Overview

```text
Applications       Outreach
      87               54

In Review           Replies
      14                9

Interviews           Offers
       6                1
```

## Application table

```text
Company | Role | Submitted | Status | Last update
```

## Outreach table

```text
Company | Contact | Sent | Status | Last update
```

## Timeline

```text
Oct 1  Application submitted — Company A
Oct 1  Founder outreach sent — Company B
Oct 2  Recruiter contacted — Company A
Oct 2  Interview scheduled — Company A
```

Counters must be derived from server-side queries, not maintained independently in the frontend.

---

# 13. Admin Dashboard

The admin system should optimize HTF operations.

Required views:

### Client list

```text
Client
Plan
Campaign
Status
Applications
Outreach
Issues
Last activity
```

### Campaign workspace

```text
Candidate profile
Campaign configuration
Applications
Outreach
Tasks
Events
Internal notes
```

### Task queue

```text
Task
Priority
Candidate
Age
Assignee
Status
```

### Payments

```text
Candidate
Plan
Amount due
Payment status
Verified by
Verified at
```

---

# 14. Authentication

Recommended design:

```text
Next.js
  │
  ▼
Clerk
  │
  ▼
Authenticated token
  │
  ▼
Django auth adapter
  │
  ▼
Local User
  │
  ▼
Role + object permissions
```

Clerk supports Google OAuth/social connections. Django should validate authenticated requests and map the external subject to the internal user. citeturn747893search0turn747893search4turn747893search9

Keep the authorization model local to HTF.

Do not rely on frontend UI hiding as a security control.

---

# 15. Authorization Model

A client can:

```text
read own profile
update own profile
read own campaigns
read own applications
read own outreach
read own events
```

A client cannot:

```text
read another candidate
read operator notes
read another campaign
change campaign status arbitrarily
change billing state
assign operator tasks
```

Operators can:

```text
read assigned operational data
manage applications
manage outreach
create/complete tasks
update campaign operational state
```

Admins can manage the entire operational dataset.

Use object-level permission checks on every read/write path where ownership matters.

---

# 16. AWS S3

Use a private bucket.

Upload pattern:

```text
Browser
   ↓
POST /api/v1/resumes/upload-url
   ↓
Django authorizes upload
   ↓
Presigned S3 URL
   ↓
Browser uploads directly to S3
   ↓
Django stores S3 object key
```

Never make sensitive resume files public.

Store object keys, not public URLs.

Recommended key format:

```text
candidates/{candidate_id}/resumes/{resume_id}/original.pdf
```

---

# 17. Celery

Celery handles work that should not block HTTP requests.

Initial task categories:

```text
resume.parse
ai.profile_extract
ai.job_match
ai.outreach_draft
notifications.email
analytics.recalculate
campaign.scheduled_check
```

The task should call a service:

```python
@app.task

def parse_resume(resume_id):
    ResumeService.parse(resume_id)
```

Do not place significant business logic in the task function.

## Idempotency

Every task must be safe to retry.

Example:

```text
resume parse task starts
      ↓
check parse_status
      ↓
if already complete → return
      ↓
process
      ↓
commit result
```

Use idempotency keys for operations that could otherwise create duplicates.

---

# 18. Transactional Consistency

Use Django transactions around multi-object business mutations.

Example:

```python
with transaction.atomic():
    application.transition_to(SUBMITTED)
    Event.objects.create(
        aggregate_type="application",
        aggregate_id=application.id,
        event_type="APPLICATION_SUBMITTED",
    )
```

Publish dependent Celery work only after commit:

```python
transaction.on_commit(
    lambda: notify_application_submitted.delay(application.id)
)
```

This avoids workers observing uncommitted state.

---

# 19. AI Architecture

```text
Django Service
      ↓
AI Service abstraction
      ↓
PydanticAI
      ↓
OmniRoute
      ↓
Model
```

The Django business layer should ask for capabilities rather than a specific model.

Bad:

```python
openai_client.responses.create(...)
```

inside business logic.

Better:

```python
AIService.match_job(candidate_id, job_id)
```

Then:

```text
AIService
   ↓
PydanticAI agent
   ↓
OmniRoute
   ↓
selected model
```

## Agents

### ProfileAgent

Input:

```text
resume
intake answers
```

Output:

```text
CandidateProfile schema
```

### JobMatchAgent

Input:

```text
candidate
job
```

Output:

```python
JobMatchResult
```

### OutreachAgent

Input:

```text
candidate
company
contact
```

Output:

```text
OutreachDraft
```

### QAAgent

Input:

```text
candidate facts
candidate-generated content
```

Output:

```text
PASS
REVIEW
REJECT
```

## AI safety rule

**AI proposes. Deterministic application code decides.**

The LLM must not directly:

- change a billing state
- grant permissions
- mark payments as received
- submit a job application
- send external communication
- delete candidate records

without going through a controlled application service/tool boundary.

---

# 20. AI Tool Contracts

Each agent receives only the tools it needs.

Example:

```text
JobMatchAgent
 ├── get_candidate_profile
 ├── get_job
 ├── get_resume_summary
 └── save_match_result
```

Example:

```text
OutreachAgent
 ├── get_candidate_profile
 ├── get_company
 ├── get_contact
 ├── check_duplicate_outreach
 └── save_draft
```

Do not give agents arbitrary database access.

---

# 21. Events & Audit

Important business changes create events.

Example:

```text
APPLICATION_SUBMITTED
APPLICATION_STATUS_CHANGED
OUTREACH_SENT
OUTREACH_REPLIED
INTERVIEW_SCHEDULED
PAYMENT_MARKED_RECEIVED
CAMPAIGN_PAUSED
```

Event structure:

```json
{
	"aggregate_type": "application",
	"aggregate_id": "uuid",
	"event_type": "APPLICATION_SUBMITTED",
	"actor_type": "operator",
	"actor_id": "uuid",
	"payload": {}
}
```

Events are useful for:

- dashboard timelines
- notifications
- analytics
- auditing
- debugging
- future integrations

Do not turn this into Kafka/event-driven microservices in v1. PostgreSQL-backed events are sufficient.

---

# 22. WhatsApp

## v1

Use WhatsApp Business App manually.

WhatsApp states that the Business app is free to download and intended for small businesses communicating with customers. citeturn105091search0turn105091search2

The software should still define:

```text
Notification
NotificationTemplate
ConversationReference
```

so the provider can be automated later.

## Future

```text
NotificationService
       ↓
WhatsAppAdapter
       ↓
Official WhatsApp Business Platform/provider
```

No unofficial WhatsApp Web automation should become a hidden dependency of the system.

---

# 23. Resend

Use Resend only for transactional email initially.

Examples:

```text
Welcome
Profile verified
Campaign started
Important campaign update
Interview notification
Payment reminder
```

Keep future client outreach mail infrastructure separate from transactional mail.

---

# 24. Manual Payments

Do not integrate a payment gateway in v1.

Flow:

```text
Client chooses plan
       ↓
WhatsApp conversation
       ↓
HTF provides QR/UPI
       ↓
Client pays
       ↓
Operator verifies payment
       ↓
Admin clicks "Mark received"
       ↓
Payment record
       ↓
Campaign billing status updated
```

The payment domain should still exist now so a future Razorpay/Stripe adapter can replace the manual verification path.

---

# 25. API Design

Use `/api/v1/` from day one.

```text
/api/v1/auth/
/api/v1/candidate/
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

Example:

```text
GET   /api/v1/campaigns
POST  /api/v1/campaigns
GET   /api/v1/campaigns/{id}
POST  /api/v1/campaigns/{id}/start
POST  /api/v1/campaigns/{id}/pause
POST  /api/v1/campaigns/{id}/resume

GET   /api/v1/campaigns/{id}/applications
GET   /api/v1/campaigns/{id}/outreach
GET   /api/v1/campaigns/{id}/events
GET   /api/v1/campaigns/{id}/metrics

GET   /api/v1/admin/tasks
POST  /api/v1/admin/tasks/{id}/claim
POST  /api/v1/admin/tasks/{id}/complete
```

Prefer action endpoints for meaningful state transitions instead of exposing unrestricted `PATCH status=` everywhere.

---

# 26. API Error Model

Standardize errors:

```json
{
	"code": "CAMPAIGN_NOT_ACTIVE",
	"message": "Campaign must be active before this operation.",
	"details": {}
}
```

Frontend should branch on `code`, not scrape error-message strings.

---

# 27. Database Constraints & Indexes

Critical constraints:

```text
unique identity provider subject
unique source + external job ID
unique candidate + job application
foreign keys on core relations
```

Indexes should initially target common queries:

```text
campaign_id
candidate_id
status
created_at
company_id
external_source + external_id
```

Add more indexes only after query plans show a need.

---

# 28. Security

Minimum baseline:

```text
HTTPS
private S3
signed URLs
secret management
role-based permissions
object-level ownership checks
CSRF protection where applicable
secure cookies/tokens
input validation
upload size/type restrictions
audit logging
encrypted backups
Sentry PII filtering
```

Never commit:

```text
.env
API keys
OAuth client secrets
S3 credentials
Clerk secrets
OmniRoute keys
```

Do not store candidate passwords for external services.

---

# 29. Observability

Sentry on:

```text
client-web
admin-web
Django
Celery workers
```

Capture:

- exceptions
- failed tasks
- external integration failures
- performance problems
- important workflow failures

Filter sensitive data from telemetry.

Potential future addition:

```text
OpenTelemetry
```

only when deeper distributed tracing becomes valuable.

---

# 30. Testing Strategy

## Unit

Test:

```text
state transitions
permission policies
campaign rules
billing rules
matching policies
selectors
services
```

## API integration

Test:

```text
authentication
authorization
CRUD
state transitions
ownership isolation
```

## Database

Test against PostgreSQL rather than relying only on SQLite.

## Celery

Test:

```text
retry behavior
idempotency
after-commit behavior
failure handling
```

## Frontend

Test critical user journeys:

```text
sign in
complete onboarding
upload resume
view campaign
view applications
view outreach
```

## E2E

Keep a small number of full-flow tests covering revenue-critical and trust-critical workflows.

---

# 31. Docker

Local services:

```text
client-web
admin-web
backend
celery-worker
postgres
redis
```

Recommended development layout:

```text
docker-compose.yml

backend/Dockerfile
client-web/Dockerfile
admin-web/Dockerfile
```

Do not put production secrets into the Docker image.

---

# 32. Initial Docker Compose Topology

```text
                   docker compose

 ┌───────────┐    ┌──────────┐
 │ client-web│    │admin-web │
 └─────┬─────┘    └────┬─────┘
       │               │
       └───────┬───────┘
               ▼
          ┌─────────┐
          │ backend │
          └────┬────┘
               │
       ┌───────┴────────┐
       ▼                ▼
  ┌─────────┐      ┌─────────┐
  │ postgres│      │  redis  │
  └─────────┘      └────┬────┘
                        ▼
                  ┌──────────┐
                  │  worker  │
                  └──────────┘
```

---

# 33. Development Milestones

## Milestone 0 — Foundation

Deliver:

- monorepo
- Docker Compose
- Django
- PostgreSQL
- Redis
- Celery
- Next.js client
- Next.js admin
- environment configuration
- linting
- formatting
- pytest
- Sentry

Definition of done:

```bash
docker compose up --build
```

starts the complete local stack.

---

## Milestone 1 — Identity

Deliver:

- Clerk
- Google OAuth
- local Django User mapping
- role system
- permission policies
- client/admin route guards

Definition of done:

A client cannot access another client's data.

---

## Milestone 2 — Candidate Onboarding

Deliver:

- candidate profile
- intake form
- resume upload
- S3
- resume metadata
- profile completion state
- operator review

Definition of done:

A client can become "campaign ready" after completing onboarding.

---

## Milestone 3 — Campaigns

Deliver:

- campaign creation
- plan selection
- trial metadata
- lifecycle
- settings
- versioning
- campaign activity

Definition of done:

An operator can activate/pause/resume a campaign.

---

## Milestone 4 — Applications

Deliver:

- company
- job
- application
- deduplication
- application state machine
- operator workspace
- application timeline
- metrics

Definition of done:

An operator can manually submit and accurately record an application end-to-end.

---

## Milestone 5 — Human Task Queue

Deliver:

- task creation
- task assignment
- claiming
- completion
- priority
- queue filters

Definition of done:

Operators can work from one queue instead of hunting through campaigns.

---

## Milestone 6 — Outreach

Deliver:

- company contacts
- outreach
- suppression list
- duplicate checks
- templates
- manual send recording
- reply tracking

Definition of done:

A complete cold-outreach campaign can be recorded and measured.

---

## Milestone 7 — Dashboards

Deliver:

- client overview
- applications table
- outreach table
- timeline
- metrics
- campaign status

Admin:

- client list
- campaign list
- task queue
- payment queue
- operational views

---

## Milestone 8 — Notifications

Deliver:

- notification model
- templates
- Resend
- interview notifications
- campaign notifications
- payment reminders

WhatsApp remains manual.

---

## Milestone 9 — Manual Billing

Deliver:

- payment model
- manual verification
- QR/UPI instructions
- trial expiry
- billing status
- admin verification

---

## Milestone 10 — AI Foundation

Deliver:

- AI service abstraction
- OmniRoute integration
- PydanticAI setup
- structured outputs
- prompt versioning
- AI execution records
- ProfileAgent
- JobMatchAgent
- OutreachAgent
- QAAgent

Definition of done:

AI accelerates operator work without independently performing external actions.

---

# 34. First AI Use Cases

Do not start with autonomous agents.

Start with narrow, measurable tasks.

## Resume extraction

```text
Resume PDF
   ↓
Parser
   ↓
ProfileAgent
   ↓
CandidateProfile draft
   ↓
Operator approves
```

## Job matching

```text
CandidateProfile
      +
Job description
      ↓
JobMatchAgent
      ↓
score + reasons + concerns
      ↓
Operator
```

## Outreach draft

```text
Candidate facts
Company facts
Contact role
      ↓
OutreachAgent
      ↓
Draft
      ↓
QAAgent
      ↓
Operator sends manually
```

---

# 35. Future Automation Seam

Every external action should already have an abstraction.

Current:

```text
ApplicationService
      ↓
Operator
      ↓
External website
```

Future:

```text
ApplicationService
      ↓
ExecutionGateway
      ├── HumanExecutor
      └── ApprovedIntegrationExecutor
```

Same principle for outreach.

The domain should not care whether the execution was done manually or through an approved integration.

---

# 36. Avoiding Agent Loops

The multi-agent system should not allow unrestricted agent-to-agent recursion.

Use a central orchestrator:

```text
                Orchestrator
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Profile        Match       Outreach
       Agent        Agent         Agent
        │            │            │
        └────────────┼────────────┘
                     ▼
                   QA
                     │
                     ▼
                  Result
```

Each agent:

- receives a typed input
- calls limited tools
- returns typed output
- has an execution budget
- has retry limits
- has a prompt version

No agent should create arbitrary new agent calls indefinitely.

---

# 37. AI Execution Record

Persist enough metadata to debug and measure AI usage.

```text
id
agent_name
agent_version
prompt_version
provider
model
workflow_id
input_reference
output_reference
input_tokens
output_tokens
latency_ms
status
error_code
created_at
```

Do not blindly store full PII-heavy prompts/outputs indefinitely. Store references or redacted records where possible.

---

# 38. Metrics

## Operational

```text
applications/day
outreach/day
operator tasks/day
average task age
application failure rate
```

## Funnel

```text
jobs discovered
jobs shortlisted
applications submitted
applications in review
interviews
offers
```

```text
contacts identified
outreach sent
replies
positive replies
interviews
```

## Product

```text
trial started
trial completed
paid campaign started
campaign paused
campaign churned
```

## Cost

```text
AI cost/campaign
email cost/campaign
storage/candidate
operator minutes/campaign
```

The long-term product metric should be campaign outcomes relative to effort, not raw application volume alone.

---

# 39. Important Product Rules

## Rule 1 — Do not promise hiring outcomes

HTF controls campaign execution, not employer decisions.

## Rule 2 — Every application needs a source

Record where the job came from.

## Rule 3 — Every external action needs an actor

```text
operator
system
future integration
```

## Rule 4 — Every important state change creates an event

## Rule 5 — Every retry must be safe

## Rule 6 — Candidate facts have one canonical source

## Rule 7 — No arbitrary LLM database writes

## Rule 8 — No third-party passwords stored

---

# 40. Repository Delivery Order

Start coding in this order:

```text
01  repository bootstrap
02  docker compose
03  Django settings
04  PostgreSQL
05  Redis
06  Celery
07  Clerk + Google OAuth
08  User/roles
09  CandidateProfile
10  Resume + S3
11  Campaign
12  Company
13  Job
14  Application
15  Application state machine
16  Event/Audit
17  HumanTask
18  Contact
19  Outreach
20  Notifications
21  Billing
22  Client UI
23  Admin UI
24  Sentry hardening
25  AI service
26  OmniRoute
27  PydanticAI agents
28  AI-assisted operator workflows
```

---

# 41. Definition of Done — HTF v1

The MVP is ready for controlled real users when:

```text
Client signs in
      ↓
Completes intake
      ↓
Uploads resume
      ↓
HTF reviews profile
      ↓
Campaign activated
      ↓
Operator works application queue
      ↓
Operator works outreach queue
      ↓
Every action is recorded
      ↓
Dashboard is accurate
      ↓
Client receives important updates
      ↓
Payment can be verified manually
```

The core acceptance criterion is:

> **At any moment, HTF can open a campaign and reconstruct what work was done, who did it, when it happened, and what happened afterward.**
