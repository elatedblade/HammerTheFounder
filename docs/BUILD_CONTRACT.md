# HTF v1 implementation contract

Shared integration contract for the current build. Implementation details and setup belong in PROJECT_GUIDE.md.

Implemented status and verification: `DELIVERY_STATUS.md`. Runtime schemas and
explicit state maps live in `backend/apps/operations/serializers.py` and
`services.py`. Expanded application/outreach states from the plan are supported;
`SAVED/READY` and `DRAFT/READY` remain compatible shorthand paths. Interview
scheduling uses `interview_scheduled_at` (ISO timestamp); scheduling requires a
future time. Application failure and outreach bounce transitions require notes.

## Conventions

- Base `/api/v1/`, trailing slash. Bearer auth; existing error envelope `{code,message,details}`.
- List responses are plain JSON arrays (bounded server-side; optional `limit`/`offset`), not invented metrics.
- Client-visible data never includes internal notes, audit payloads, or storage keys.
- Operational roles OPERATOR/ADMIN/SUPERADMIN. Admins see all; operators see assigned campaigns and unassigned intake campaigns. Assignment changes admin-only.
- Preserve existing campaign and candidate endpoints/contracts. UUIDs for new business objects; existing candidate/user integer IDs.
- Mutation endpoints return updated object, creation 201; conflicts 409. Explicit transition actions with `{status,notes?}`.

## Operations (T1)

- `GET /admin/candidates/` returns candidate profile fields plus `user_id,email,review_status,review_notes,reviewed_at`.
- `GET/PATCH /admin/candidates/{id}/` operational read/edit; PATCH review `{review_status:APPROVED|CHANGES_REQUESTED,review_notes}`.
- Candidate self-service profile adds optional intake fields `target_industries:string[],expected_ctc_min:number|null,expected_ctc_max:number|null,work_authorization:string,sponsorship_requirement:string,notice_period:string,preferences_json:object`; read-only `review_status`.
- `GET /admin/operators/` returns `{id,email,role}` for assignment.
- Existing `/campaigns/` and lifecycle routes remain. PATCH `/campaigns/{id}/` for plan/settings/trial and admin-only `assigned_to:number|null`; POST `complete/`, `cancel/`.
- Campaign output adds `candidate_name,candidate_email,assigned_to` for operational users where appropriate.
- `GET/POST /companies/`; `GET/PATCH /companies/{id}/`: `{id,name,website,industry,location}`.
- `GET/POST /jobs/`; `GET/PATCH /jobs/{id}/`: `{id,company,company_name,title,canonical_url,external_source,external_id,location,employment_type,description,status}`. Filters `company,status,q`.
- `GET/POST /applications/`; `GET/PATCH /applications/{id}/`; POST `{id}/transition/`: `{id,campaign,job,company_name,job_title,status,submitted_at,notes,source_reference,created_at,updated_at}`. Client own reads only; notes operational only. Filter `campaign,status`.
- `GET/POST /contacts/`; `GET/PATCH /contacts/{id}/`: `{id,company,company_name,name,title,email,profile_url,source}`.
- `GET/POST /suppression/`: `{id,email,reason,created_at}`; operational only.
- `GET/POST /outreach/`; `GET/PATCH /outreach/{id}/`; POST `{id}/transition/`: `{id,campaign,contact,company_name,contact_name,channel,status,subject,body,sent_at,reply_at,follow_up_due_at,thread_reference,notes}`. Client own reads sanitized.
- `GET/POST /outreach/templates/`: `{id,name,subject,body}` operational templates.
- `GET/POST /admin/tasks/`; `POST /admin/tasks/{id}/claim/`; `POST .../complete/` `{notes?}`; PATCH task for admin assignment/priority: `{id,campaign,task_type,priority,status,assigned_to,payload_json,created_at,completed_at}`.
- `GET /campaigns/{id}/applications/`, `/outreach/`, `/events/`, `/metrics/` scoped aliases.
- `GET /dashboard/` scoped aggregates: `{applications:{total,submitted,in_review,interviews,offers,rejected},outreach:{total,sent,replies,positive_replies,bounced},campaigns:{total,active},tasks:{open}}`.
- `GET /events/?campaign=` returns client-safe event timeline `{id,event_type,summary,created_at,campaign}`; audit detail operational only.
- Events integration for T2: `apps.events.services.record_event(*,campaign=None,event_type,actor=None,summary,payload=None,client_visible=True)` accepts campaign object; transactional DB write, no external side effects.
- Scope integration for T2: `apps.campaigns.selectors.get_visible_campaigns(user)` and `get_visible_campaign(user,id)`.

## Supporting services (T2)

- `GET/POST /billing/payments/`; `POST /billing/payments/{id}/verify/` `{reference,notes?}` admin-only; `POST .../transition/` admin-only for FAILED/REFUNDED. Fields `{id,campaign,amount,currency,status,reference,notes,verified_by,verified_at,created_at}`. Client own read sanitized. Decimal amounts serialize as strings. POST operational creates pending record, server owns verification/status.
- `GET /billing/instructions/` returns `{configured,upi_id,payee_name,instructions}` from environment, no fabricated payment address.
- `GET /notifications/` client own or operational scoped list; `POST /notifications/` operational `{campaign,channel,recipient,subject,body}`; POST `{id}/send/` transactional email only; POST `{id}/mark-sent/` manual WhatsApp recording. Fields `{id,campaign,channel,status,subject,body,created_at,sent_at}`. No automatic cold outreach.
- `GET/POST /notifications/templates/` operational `{id,name,channel,subject,body}`.
- `GET /admin/candidates/{id}/resumes/` scoped operational metadata; `POST /resumes/{id}/download/` owned client or authorized operator signed download `{url,expires_in}`; `POST /resumes/{id}/parse/` operational queued parsing.
- `GET /resumes/{id}/parsed-text/` operational-only extracted preview `{text,truncated,...}` capped at 32,000 characters; no-store.
- `GET/POST /ai/runs/` operational; POST `{campaign,capability:profile_extract|job_match|outreach_draft|qa,input:object}` records/enqueues bounded typed AI assistance. `GET /ai/runs/{id}/` poll `{id,campaign,capability,status,result,error_code,created_at}`. Configuration missing returns 503, not simulated output. Results are proposals only, never auto-mutate profiles or send outreach. Avoid raw PII in telemetry.
- AI input keys are strictly `profile_extract:{resume_id}`, `job_match:{job_id}`, `outreach_draft:{contact_id}`, `qa:{content}`. Candidate facts always come from the database; input overrides are rejected.
- Background tasks for notifications, resume parsing, AI, trial expiry; external integrations have timeouts, bounded retries, idempotency/state checks. Provide explicit management command for trial expiry if no scheduler is configured.
- T2 report environment/dependency/config additions to main; do not edit shared settings/urls/pyproject/compose.

## Frontends

- Admin (T3): tabbed operational workspace: candidates/review, campaigns, companies/jobs/applications, contacts/outreach/suppression/templates, tasks, billing, communications, AI proposals; campaign selection scopes records; show real timeline and metrics. Use APIs above; no fake buttons or success. Forms validate and render API field errors.
- Candidate (T4): retain profile/resume/campaign features; add complete intake fields, resume download, application/outreach tables, interviews, activity, real overview metrics, notifications, payment status/instructions. Never expose operator-only fields/actions. Usable empty/loading/error states.
- Both: accessible responsive UI in existing stack; no external actions or payments performed automatically. No extra dependencies without need.
